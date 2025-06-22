#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebLoginBrute 会话管理模块
提供会话轮换、会话池管理和会话生命周期控制
"""

import logging
import time
import random
from typing import Dict, Any, Optional
from dataclasses import dataclass
from threading import Lock, Timer

import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..constants import USER_AGENTS, BROWSER_HEADERS

# 初始化日志
log = logging.getLogger(__name__)


@dataclass
class SessionConfig:
    """会话配置"""

    rotation_interval: int = 300  # 会话轮换间隔(秒)
    session_lifetime: int = 600  # 会话生命周期(秒)
    max_session_pool_size: int = 100  # 最大会话池大小
    enable_rotation: bool = True  # 是否启用会话轮换
    rotation_strategy: str = "time"  # 轮换策略: time, request_count, error_rate


class SessionInfo:
    """会话信息"""

    def __init__(self, session: Session, created_time: float):
        self.session = session
        self.created_time = created_time
        self.last_used = created_time
        self.request_count = 0
        self.error_count = 0
        self.success_count = 0
        self.rotation_count = 0

    @property
    def age(self) -> float:
        """会话年龄(秒)"""
        return time.time() - self.created_time

    @property
    def idle_time(self) -> float:
        """空闲时间(秒)"""
        return time.time() - self.last_used

    @property
    def error_rate(self) -> float:
        """错误率"""
        total_requests = self.request_count
        return self.error_count / total_requests if total_requests > 0 else 0.0

    @property
    def success_rate(self) -> float:
        """成功率"""
        total_requests = self.request_count
        return self.success_count / total_requests if total_requests > 0 else 0.0


class SessionRotator:
    """会话轮换器"""

    def __init__(self, config: Optional[SessionConfig] = None):
        self.config = config or SessionConfig()
        self.lock = Lock()
        self._session_pool: Dict[str, SessionInfo] = {}
        self._rotation_timer = None
        self._monitoring = False

        # 轮换统计
        self.stats = {
            "total_rotations": 0,
            "forced_rotations": 0,
            "session_creations": 0,
            "session_cleanups": 0,
            "last_rotation": time.time(),
        }

        if self.config.enable_rotation:
            self.start_rotation_monitoring()

    def start_rotation_monitoring(self):
        """开始会话轮换监控"""
        if self._monitoring:
            return

        self._monitoring = True
        self._schedule_rotation()
        log.info("会话轮换监控已启动")

    def stop_rotation_monitoring(self):
        """停止会话轮换监控"""
        self._monitoring = False
        if self._rotation_timer:
            self._rotation_timer.cancel()
            self._rotation_timer = None
        log.info("会话轮换监控已停止")

    def _schedule_rotation(self):
        """安排下一次轮换检查"""
        if not self._monitoring:
            return

        self._rotation_timer = Timer(
            self.config.rotation_interval, self._check_rotations
        )
        self._rotation_timer.daemon = True
        self._rotation_timer.start()

    def _check_rotations(self):
        """检查并执行会话轮换"""
        try:
            with self.lock:
                sessions_to_rotate = []

                for session_key, session_info in self._session_pool.items():
                    should_rotate = False
                    rotation_reason = ""

                    # 检查轮换条件
                    if self.config.rotation_strategy == "time":
                        if session_info.age > self.config.session_lifetime:
                            should_rotate = True
                            rotation_reason = "会话超时"
                    elif self.config.rotation_strategy == "request_count":
                        if session_info.request_count > 1000:  # 请求数阈值
                            should_rotate = True
                            rotation_reason = "请求数过多"
                    elif self.config.rotation_strategy == "error_rate":
                        if session_info.error_rate > 0.3:  # 错误率阈值
                            should_rotate = True
                            rotation_reason = "错误率过高"

                    # 检查空闲时间
                    if session_info.idle_time > self.config.session_lifetime * 2:
                        should_rotate = True
                        rotation_reason = "会话空闲"

                    if should_rotate:
                        sessions_to_rotate.append((session_key, rotation_reason))

                # 执行轮换
                for session_key, reason in sessions_to_rotate:
                    self._rotate_session(session_key, reason)

                # 清理过期会话
                self._cleanup_expired_sessions()

        except Exception as e:
            log.error(f"会话轮换检查失败: {e}")
        finally:
            # 安排下一次检查
            self._schedule_rotation()

    def _rotate_session(self, session_key: str, reason: str):
        """轮换指定会话"""
        try:
            session_info = self._session_pool[session_key]

            # 关闭旧会话
            try:
                session_info.session.close()
            except Exception as e:
                log.debug(f"关闭会话失败: {e}")

            # 创建新会话
            new_session = self._create_new_session()
            new_session_info = SessionInfo(new_session, time.time())
            new_session_info.rotation_count = session_info.rotation_count + 1

            # 替换会话
            self._session_pool[session_key] = new_session_info

            self.stats["total_rotations"] += 1
            log.info(f"会话轮换完成: {session_key} - {reason}")

        except Exception as e:
            log.error(f"会话轮换失败: {session_key} - {e}")

    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = time.time()
        expired_sessions = []

        for session_key, session_info in self._session_pool.items():
            if (
                current_time - session_info.created_time
                > self.config.session_lifetime * 2
            ):
                expired_sessions.append(session_key)

        for session_key in expired_sessions:
            try:
                session_info = self._session_pool[session_key]
                session_info.session.close()
                del self._session_pool[session_key]
                self.stats["session_cleanups"] += 1
                log.debug(f"清理过期会话: {session_key}")
            except Exception as e:
                log.error(f"清理会话失败: {session_key} - {e}")

    def _create_new_session(self) -> Session:
        """创建新会话"""
        session = requests.Session()
        session.max_redirects = 5

        # 设置随机User-Agent
        session.headers.update({"User-Agent": random.choice(USER_AGENTS)})  # nosec B311

        # 设置浏览器头
        for key, value in BROWSER_HEADERS.items():
            session.headers.setdefault(key, value)

        # 加载cookies (如果配置了cookie文件)
        # 这里可以根据session_key解析出cookie文件路径
        # 暂时跳过cookie加载，可以在具体使用时配置

        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        self.stats["session_creations"] += 1
        return session

    def get_session(self, session_key: str) -> Session:
        """获取或创建会话"""
        with self.lock:
            if session_key in self._session_pool:
                session_info = self._session_pool[session_key]

                # 检查会话是否仍然有效
                if session_info.age < self.config.session_lifetime:
                    session_info.last_used = time.time()
                    return session_info.session
                else:
                    # 会话过期，轮换
                    self._rotate_session(session_key, "会话过期")

            # 创建新会话
            session = self._create_new_session()
            session_info = SessionInfo(session, time.time())

            # 添加到会话池
            self._session_pool[session_key] = session_info

            # 限制会话池大小
            if len(self._session_pool) > self.config.max_session_pool_size:
                self._remove_oldest_session()

            return session

    def _remove_oldest_session(self):
        """移除最旧的会话"""
        if not self._session_pool:
            return

        oldest_key = min(
            self._session_pool.keys(), key=lambda k: self._session_pool[k].created_time
        )

        try:
            session_info = self._session_pool[oldest_key]
            session_info.session.close()
            del self._session_pool[oldest_key]
            log.debug(f"移除最旧会话: {oldest_key}")
        except Exception as e:
            log.error(f"移除会话失败: {oldest_key} - {e}")

    def record_request(self, session_key: str, success: bool = True):
        """记录请求结果"""
        with self.lock:
            if session_key in self._session_pool:
                session_info = self._session_pool[session_key]
                session_info.request_count += 1
                session_info.last_used = time.time()

                if success:
                    session_info.success_count += 1
                else:
                    session_info.error_count += 1

    def force_rotate_session(self, session_key: str, reason: str = "强制轮换"):
        """强制轮换会话"""
        with self.lock:
            if session_key in self._session_pool:
                self._rotate_session(session_key, reason)
                self.stats["forced_rotations"] += 1

    def get_session_stats(self, session_key: str) -> Optional[Dict[str, Any]]:
        """获取会话统计信息"""
        with self.lock:
            if session_key in self._session_pool:
                session_info = self._session_pool[session_key]
                return {
                    "age": session_info.age,
                    "idle_time": session_info.idle_time,
                    "request_count": session_info.request_count,
                    "error_count": session_info.error_count,
                    "success_count": session_info.success_count,
                    "error_rate": session_info.error_rate,
                    "success_rate": session_info.success_rate,
                    "rotation_count": session_info.rotation_count,
                }
        return None

    def get_pool_stats(self) -> Dict[str, Any]:
        """获取会话池统计信息"""
        with self.lock:
            total_sessions = len(self._session_pool)
            total_requests = sum(si.request_count for si in self._session_pool.values())
            total_errors = sum(si.error_count for si in self._session_pool.values())

            return {
                "total_sessions": total_sessions,
                "total_requests": total_requests,
                "total_errors": total_errors,
                "avg_error_rate": (
                    total_errors / total_requests if total_requests > 0 else 0.0
                ),
                "rotation_stats": self.stats.copy(),
            }

    def cleanup(self):
        """清理所有会话"""
        self.stop_rotation_monitoring()

        with self.lock:
            for session_key, session_info in self._session_pool.items():
                try:
                    session_info.session.close()
                except Exception as e:
                    log.debug(f"关闭会话失败: {session_key} - {e}")

            self._session_pool.clear()
            log.info("所有会话已清理")


# 全局会话轮换器实例
_global_session_rotator: Optional[SessionRotator] = None
_lock = Lock()


def get_session_rotator(config: Optional[SessionConfig] = None) -> SessionRotator:
    """获取全局会话轮换器"""
    global _global_session_rotator
    if _global_session_rotator is None:
        with _lock:
            if _global_session_rotator is None:
                _global_session_rotator = SessionRotator(config)
    return _global_session_rotator


def init_session_rotator(config: Optional[SessionConfig] = None) -> SessionRotator:
    """初始化会话轮换器"""
    global _global_session_rotator
    if _global_session_rotator:
        _global_session_rotator.cleanup()

    _global_session_rotator = SessionRotator(config)
    return _global_session_rotator
