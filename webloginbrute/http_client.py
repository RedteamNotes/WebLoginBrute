#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import http.cookiejar as cookielib
import logging
import random
import socket
import time
from threading import Lock
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import requests
from requests import Session

from .constants import USER_AGENTS, BROWSER_HEADERS
from .exceptions import NetworkError
from .session_manager import get_session_rotator, SessionConfig
from .memory_manager import get_memory_manager

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
        
        # 重试配置
        self.max_retries = getattr(config, 'max_retries', 3)
        self.base_delay = getattr(config, 'base_delay', 1.0)
        
        # 获取会话轮换器和内存管理器
        self.session_rotator = get_session_rotator()
        self.memory_manager = get_memory_manager()
        
        # 会话配置
        session_config = SessionConfig(
            rotation_interval=getattr(config, 'session_rotation_interval', 300),
            session_lifetime=getattr(config, 'session_lifetime', 600),
            max_session_pool_size=getattr(config, 'max_session_pool_size', 100),
            enable_rotation=getattr(config, 'enable_session_rotation', True),
            rotation_strategy=getattr(config, 'rotation_strategy', 'time')
        )
        
        # 初始化会话轮换器
        self.session_rotator.config = session_config

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
        session_key = f"{parsed_url.scheme}://{hostname}:{parsed_url.port or 80}"

        # 从会话轮换器获取会话
        cookie_file = getattr(self.config, 'cookie', None)
        session = self.session_rotator.get_session(session_key, cookie_file)
        
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
                # 检查内存使用
                with self.memory_manager.memory_context():
                    response = session.request(method, url, **kwargs)
                    response.raise_for_status()  # 对 4xx 或 5xx 状态码抛出异常
                    
                    # 验证响应头的安全性
                    if not self._validate_response_headers(response):
                        raise NetworkError("响应头安全检查失败")
                    
                    # 记录成功请求
                    self.session_rotator.record_request(session_key, success=True)
                    
                    return response

            except requests.exceptions.Timeout as e:
                last_exception = NetworkError(f"请求超时: {url}")
                logging.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries + 1}): {url}")
                self.session_rotator.record_request(session_key, success=False)
            except requests.exceptions.ConnectionError as e:
                last_exception = NetworkError(f"连接错误: {url} - {e}")
                logging.warning(f"连接错误 (尝试 {attempt + 1}/{self.max_retries + 1}): {url}")
                self.session_rotator.record_request(session_key, success=False)
            except requests.exceptions.HTTPError as e:
                # HTTP错误通常意味着请求已到达服务器，但因客户端或服务器错误而被拒绝
                # 这类错误通常不应该重试，直接向上抛出
                error_msg = f"HTTP错误: {e.response.status_code} - {url}"
                if e.response.status_code == 429:
                    error_msg += " (频率限制)"
                    # 频率限制时强制轮换会话
                    self.session_rotator.force_rotate_session(session_key, "频率限制")
                elif e.response.status_code >= 500:
                    error_msg += " (服务器错误)"
                
                self.session_rotator.record_request(session_key, success=False)
                raise NetworkError(error_msg) from e
            except requests.exceptions.RequestException as e:
                # 其他请求异常
                last_exception = NetworkError(f"请求异常: {url} - {e}")
                logging.error(f"请求异常: {e}")
                self.session_rotator.record_request(session_key, success=False)
            except Exception as e:
                # 未知异常
                last_exception = NetworkError(f"未知网络错误: {url} - {e}")
                logging.error(f"未知网络错误: {e}")
                self.session_rotator.record_request(session_key, success=False)

            if attempt < self.max_retries:
                delay = self.base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                logging.info(f"将在 {delay:.1f} 秒后重试...")
                time.sleep(delay)
        
        raise last_exception if last_exception else NetworkError("请求失败，已达最大重试次数")

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
            
            # 缓存结果
            with self._dns_cache_lock:
                self._dns_cache[host] = ip_str
            
            logging.debug(f"DNS解析成功: {host} -> {ip_str}")
            return ip_str
        except socket.gaierror as e:
            logging.warning(f"DNS解析失败: {host} - {e}")
            # 缓存失败结果，避免重复尝试
            with self._dns_cache_lock:
                self._dns_cache[host] = None
            return None
        except socket.timeout:
            logging.warning(f"DNS解析超时: {host}")
            with self._dns_cache_lock:
                self._dns_cache[host] = None
            return None
        except Exception as e:
            logging.error(f"DNS解析异常: {host} - {e}")
            with self._dns_cache_lock:
                self._dns_cache[host] = None
            return None

    def close_all_sessions(self):
        """关闭所有会话"""
        try:
            self.session_rotator.cleanup()
            logging.info("所有HTTP会话已关闭")
        except Exception as e:
            logging.error(f"关闭会话时发生错误: {e}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        return self.session_rotator.get_pool_stats()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        return self.memory_manager.get_memory_stats()
