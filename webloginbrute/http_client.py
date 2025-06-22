#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import random
import socket
import time
from threading import Lock
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import requests

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
        self.max_retries = getattr(config, "max_retries", 3)
        self.base_delay = getattr(config, "base_delay", 1.0)

        # 获取会话轮换器和内存管理器
        self.session_rotator = get_session_rotator()
        self.memory_manager = get_memory_manager()

        # 会话配置
        session_config = SessionConfig(
            rotation_interval=getattr(config, "session_rotation_interval", 300),
            session_lifetime=getattr(config, "session_lifetime", 600),
            max_session_pool_size=getattr(config, "max_session_pool_size", 100),
            enable_rotation=getattr(config, "enable_session_rotation", True),
            rotation_strategy=getattr(config, "rotation_strategy", "time"),
        )

        # 初始化会话轮换器
        self.session_rotator.config = session_config

    def get(
        self, url: str, headers: Optional[Dict] = None, **kwargs
    ) -> requests.Response:
        """执行带重试的GET请求"""
        return self._make_request_with_retry("GET", url, headers=headers, **kwargs)

    def post(
        self, url: str, data: Dict, headers: Optional[Dict] = None, **kwargs
    ) -> requests.Response:
        """执行带重试的POST请求"""
        return self._make_request_with_retry(
            "POST", url, data=data, headers=headers, **kwargs
        )

    def _make_request_with_retry(
        self, method: str, url: str, headers: Optional[Dict] = None, **kwargs
    ) -> requests.Response:
        """带重试的核心请求方法"""
        last_exception = None
        headers = headers or {}
        headers.setdefault("User-Agent", random.choice(USER_AGENTS))  # nosec B311
        for key, value in BROWSER_HEADERS.items():
            headers.setdefault(key, value)

        for attempt in range(self.max_retries + 1):
            try:
                session = self.session_rotator.get_session(url)
                response = session.request(method, url, headers=headers, **kwargs)
                response.raise_for_status()
                if not self._validate_response_headers(response):
                    raise NetworkError("响应头安全检查失败", url=url)
                return response
            except requests.exceptions.Timeout as e:
                last_exception = e
                logging.warning(
                    f"请求超时 (尝试 {attempt + 1}/{self.max_retries + 1}): {url}"
                )
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logging.warning(
                    f"连接错误 (尝试 {attempt + 1}/{self.max_retries + 1}): {url}"
                )
            except requests.exceptions.RequestException as e:
                last_exception = e
                logging.error(f"请求失败: {e}")
                break  # 对于其他请求异常，不重试
            except Exception as e:
                last_exception = e
                logging.error(f"请求过程中发生未知错误: {e}")
                break

            if attempt < self.max_retries:
                delay = self.base_delay * (2**attempt) + random.uniform(
                    0, 0.5
                )  # nosec B311
                logging.info(f"将在 {delay:.1f} 秒后重试...")
                time.sleep(delay)

        raise NetworkError(
            f"请求失败，已达最大重试次数: {url}",
            url=url,
            retry_count=self.max_retries,
        ) from last_exception

    def _validate_response_headers(self, response: requests.Response) -> bool:
        """验证响应头的安全性"""
        total_header_size = sum(
            len(name) + len(value) for name, value in response.headers.items()
        )
        if total_header_size > 8192:  # 8KB
            logging.warning(f"响应头过大 ({total_header_size} bytes)，可能存在风险")
            return False
        return True

    def pre_resolve_targets(self, urls: List[str]):
        """预解析目标域名，避免运行时DNS阻塞"""
        targets = set()
        for url in urls:
            if not url:
                continue
            try:
                parsed = urlparse(url)
                if parsed.hostname:
                    targets.add(parsed.hostname)
            except Exception:  # nosec B112
                # 忽略无法解析的URL，继续处理下一个
                continue

        if not targets:
            return

        logging.info(f"预解析目标域名: {', '.join(targets)}")
        for host in targets:
            self._resolve_host(host)

    def _resolve_host(self, host: str) -> Optional[str]:
        """解析主机名为IP地址，带缓存和超时"""
        if host in self._dns_cache:
            return self._dns_cache.get(host)

        try:
            # 设置socket超时
            socket.setdefaulttimeout(5.0)
            ip_str = socket.gethostbyname(host)
            self._dns_cache[host] = ip_str
            logging.debug(f"DNS解析成功: {host} -> {ip_str}")
            return ip_str
        except socket.gaierror:
            logging.warning(f"DNS解析失败: {host}")
            self._dns_cache[host] = None
            return None
        except socket.timeout:
            logging.warning(f"DNS解析超时: {host}")
            self._dns_cache[host] = None
            return None
        except Exception as e:
            logging.error(f"DNS解析异常: {host} - {e}")
            self._dns_cache[host] = None
            return None

    def close_all_sessions(self):
        """关闭所有会话"""
        try:
            self.session_rotator.cleanup()
            logging.info("所有HTTP会话已关闭")
        except Exception as e:
            logging.error(f"关闭所有会话时出错: {e}")

    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        return self.session_rotator.get_pool_stats()

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存使用统计"""
        return self.memory_manager.get_memory_stats()
