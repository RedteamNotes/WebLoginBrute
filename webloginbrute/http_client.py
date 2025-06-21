#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import http.cookiejar as cookielib
import logging
import random
import socket
import time
from threading import Lock
from typing import Optional, Dict, Any

import requests
from requests import Session

from .constants import USER_AGENTS, BROWSER_HEADERS
from .exceptions import NetworkError

class HttpClient:
    """
    一个健壮的HTTP客户端，用于处理所有网络请求。
    它包含会话管理、DNS缓存、请求重试和安全头验证等功能。
    """
    def __init__(self, config: object):
        self.config = config
        
        # DNS缓存
        self._dns_cache: Dict[str, Optional[str]] = {}
        self._dns_cache_lock = Lock()
        
        # 会话池
        self._session_pool: Dict[str, Dict[str, Any]] = {}
        self._session_pool_lock = Lock()
        
        # 重试配置
        self.max_retries = getattr(config, 'max_retries', 3)
        self.base_delay = getattr(config, 'base_delay', 1.0)
        
        self.session_lifetime = getattr(self.config, 'session_lifetime', 300)
        self.max_session_pool_size = getattr(self.config, 'max_session_pool_size', 100)

    def get(self, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """执行带重试的GET请求"""
        return self._make_request_with_retry('GET', url, headers=headers, **kwargs)

    def post(self, url: str, data: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """执行带重试的POST请求"""
        return self._make_request_with_retry('POST', url, data=data, headers=headers, **kwargs)

    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """使用指数退避策略执行请求，并管理会话"""
        last_exception = None
        
        # 解析hostname
        try:
            parsed_url = urlparse(url)
            if not parsed_url.hostname:
                raise NetworkError(f"无效的URL，无法提取hostname: {url}")
            hostname = parsed_url.hostname
        except Exception as e:
            raise NetworkError(f"URL解析失败: {url} - {e}")

        # 使用带缓存的DNS解析获取IP地址作为会话键
        session_key = self._resolve_host(hostname)
        if not session_key:
            raise NetworkError(f"DNS解析失败，无法继续请求: {hostname}")

        # 从会话池获取或创建一个会话
        session = self._get_session(session_key)
        
        # 准备请求头
        headers = kwargs.get('headers', {}).copy()
        headers.setdefault('User-Agent', random.choice(USER_AGENTS))
        for key, value in BROWSER_HEADERS.items():
            headers.setdefault(key, value)
        kwargs['headers'] = headers
        
        # 设置超时
        kwargs.setdefault('timeout', getattr(self.config, 'timeout', 30))

        for attempt in range(self.max_retries + 1):
            try:
                response = session.request(method, url, **kwargs)
                response.raise_for_status()  # 对 4xx 或 5xx 状态码抛出异常
                
                # 验证响应头的安全性
                if not self._validate_response_headers(response):
                    raise NetworkError("响应头安全检查失败")
                
                return response

            except requests.exceptions.Timeout as e:
                last_exception = NetworkError(f"请求超时: {url}")
                logging.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries + 1})")
            except requests.exceptions.ConnectionError as e:
                last_exception = NetworkError(f"连接错误: {url} - {e}")
                logging.warning(f"连接错误 (尝试 {attempt + 1}/{self.max_retries + 1})")
            except requests.exceptions.HTTPError as e:
                # HTTP错误通常意味着请求已到达服务器，但因客户端或服务器错误而被拒绝
                # 这类错误通常不应该重试，直接向上抛出
                raise NetworkError(f"HTTP错误: {e.response.status_code} - {url}") from e
            except Exception as e:
                last_exception = NetworkError(f"请求过程中发生未知错误: {e}")
                logging.error(f"未知网络错误: {e}")

            if attempt < self.max_retries:
                delay = self.base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logging.info(f"将在 {delay:.1f} 秒后重试...")
                time.sleep(delay)
        
        raise last_exception if last_exception else NetworkError("请求失败，已达最大重试次数")

    def _get_session(self, session_key: str) -> Session:
        """从会话池中获取或创建会话"""
        with self._session_pool_lock:
            if session_key in self._session_pool:
                session_info = self._session_pool[session_key]
                if time.time() - session_info['created_time'] < self.session_lifetime:
                    return session_info['session']
                else:
                    try:
                        session_info['session'].close()
                    except Exception:
                        pass
                    del self._session_pool[session_key]

            # 创建新会话
            session = requests.Session()
            session.max_redirects = 5
            
            # 加载cookies
            cookie_file = getattr(self.config, 'cookie_file', None)
            if cookie_file:
                try:
                    jar = cookielib.MozillaCookieJar(cookie_file)
                    jar.load(ignore_discard=True, ignore_expires=True)
                    session.cookies.update(jar)
                except Exception as e:
                    logging.warning(f"加载Cookie文件 '{cookie_file}' 失败: {e}")
            
            self._session_pool[session_key] = {
                'session': session,
                'created_time': time.time()
            }
            
            # 限制会话池大小
            if len(self._session_pool) > self.max_session_pool_size:
                oldest_key = min(self._session_pool.keys(), key=lambda k: self._session_pool[k]['created_time'])
                try:
                    self._session_pool[oldest_key]['session'].close()
                except Exception:
                    pass
                del self._session_pool[oldest_key]
            
            return session

    def _validate_response_headers(self, response: requests.Response) -> bool:
        """验证响应头的安全性"""
        total_header_size = sum(len(name) + len(value) for name, value in response.headers.items())
        if total_header_size > 8192:  # 8KB
            logging.warning(f"响应头过大 ({total_header_size} bytes)，可能存在风险")
            return False
        return True

    def pre_resolve_targets(self, urls: list):
        """预解析目标域名，避免运行时DNS阻塞"""
        targets = set()
        for url in urls:
            if url:
                try:
                    parsed = urlparse(url)
                    if parsed.hostname:
                        targets.add(parsed.hostname)
                except Exception:
                    continue
        
        if not targets:
            return
            
        logging.info(f"预解析目标域名: {', '.join(targets)}")
        for host in targets:
            self._resolve_host(host)

    def _resolve_host(self, host: str, timeout: float = 5.0) -> Optional[str]:
        """解析主机名为IP地址，带缓存和超时"""
        with self._dns_cache_lock:
            if host in self._dns_cache:
                return self._dns_cache[host]
        
        try:
            socket.setdefaulttimeout(timeout)
            ip_str = socket.gethostbyname(host)
            with self._dns_cache_lock:
                self._dns_cache[host] = ip_str
            logging.debug(f"DNS解析成功: {host} -> {ip_str}")
            return ip_str
        except (socket.gaierror, socket.timeout) as e:
            logging.warning(f"DNS解析失败: {host} - {e}")
            with self._dns_cache_lock:
                self._dns_cache[host] = None
            return None

    def close_all_sessions(self):
        """关闭并清理所有会话"""
        with self._session_pool_lock:
            for session_info in self._session_pool.values():
                try:
                    session_info['session'].close()
                except Exception:
                    pass
            self._session_pool.clear()
            logging.debug("所有HTTP会话已关闭")

from urllib.parse import urlparse
