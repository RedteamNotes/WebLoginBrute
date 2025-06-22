#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebLoginBrute 增强日志系统
提供结构化日志、性能监控、日志轮转、安全过滤等功能
"""

import json
import logging
import logging.handlers
import sys
import time
from datetime import datetime
from threading import Lock
import re
from typing import List, Optional, Literal, Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False



# 敏感信息字段列表
SENSITIVE_FIELDS = [
    'password', 'pass', 'pwd',
    'secret', 'token', 'apikey', 'privatekey',
    'sessionid', 'cookie', 'authorization'
]

# 敏感信息过滤的正则表达式
SENSITIVE_PATTERNS = [
    re.compile(
        r'(\b' + field + r'\b\s*[:=]\s*[\'"]?)(.*?)([\'"]?[\s,}])', re.IGNORECASE)
    for field in SENSITIVE_FIELDS
]

MASK = '***'


class SecureFormatter(logging.Formatter):
    """安全日志格式化器，自动过滤敏感信息"""

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None, style: Literal['%', '{', '$'] = '%'):
        super().__init__(fmt, datefmt, style)

    def format(self, record: logging.LogRecord) -> str:
        # 先进行标准格式化
        original_message = super().format(record)
        # 然后对格式化后的完整消息进行过滤
        return self._filter_sensitive_info(original_message)

    def _filter_sensitive_info(self, message: str) -> str:
        """过滤敏感信息"""
        if not isinstance(message, str):
            return message

        # 使用正则表达式过滤
        for pattern in SENSITIVE_PATTERNS:
            message = pattern.sub(r'\1' + MASK + r'\3', message)

        return message


class JsonFormatter(logging.Formatter):
    """JSON格式日志格式化器"""

    def __init__(self, include_timestamp=True, include_level=True, include_name=True):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_name = include_name

    def format(self, record):
        log_record = {}

        if self.include_timestamp:
            log_record['timestamp'] = datetime.fromtimestamp(record.created).isoformat()

        if self.include_level:
            log_record['level'] = record.levelname

        if self.include_name:
            log_record['logger'] = record.name

        # 清理消息
        log_record['message'] = SecureFormatter._sanitize_log_message(
            record.getMessage())

        # 添加额外字段
        if hasattr(record, 'module'):
            log_record['module'] = record.module

        if hasattr(record, 'funcName'):
            log_record['function'] = record.funcName

        if hasattr(record, 'lineno'):
            log_record['line'] = record.lineno

        if hasattr(record, 'pathname'):
            log_record['file'] = record.pathname

        # 添加异常信息
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

        # 添加自定义字段
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                           'filename', 'module', 'lineno', 'funcName', 'created',
                           'msecs', 'relativeCreated', 'thread', 'threadName',
                           'processName', 'process', 'getMessage', 'exc_info',
                           'exc_text', 'stack_info']:
                log_record[key] = value

        return json.dumps(log_record, ensure_ascii=False)


class PerformanceFormatter(logging.Formatter):
    """性能监控日志格式化器"""

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.start_times = {}
        self.lock = Lock()

    def format(self, record):
        # 添加性能指标
        if hasattr(record, 'performance_metrics'):
            with self.lock:
                if PSUTIL_AVAILABLE:
                    try:
                        process = psutil.Process()
                        # 使用setattr动态添加属性
                        setattr(record, 'performance_metrics', {
                            'cpu_percent': process.cpu_percent(),
                            'memory_mb': process.memory_info().rss / 1024 / 1024,
                            'thread_count': process.num_threads(),
                            'open_files': len(process.open_files()),
                        })
                    except Exception:  # nosec B110
                        # 在无法获取进程信息时静默失败
                        pass

        return super().format(record)


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.lock = Lock()

        # 性能指标
        self.performance_metrics = {}
        self.start_times = {}

    def _add_performance_context(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """添加性能上下文"""
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                extra['performance'] = {
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'thread_count': process.num_threads(),
                    'open_files': len(process.open_files()),
                }
            except Exception:  # nosec B110
                # 在无法获取进程信息时静默失败
                pass
        return extra

    def info(self, message: str, **kwargs):
        """记录信息日志"""
        extra = self._add_performance_context(kwargs)
        self.logger.info(message, extra=extra)

    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        extra = self._add_performance_context(kwargs)
        self.logger.warning(message, extra=extra)

    def error(self, message: str, **kwargs):
        """记录错误日志"""
        extra = self._add_performance_context(kwargs)
        self.logger.error(message, extra=extra)

    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        extra = self._add_performance_context(kwargs)
        self.logger.debug(message, extra=extra)

    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        extra = self._add_performance_context(kwargs)
        self.logger.critical(message, extra=extra)

    def start_timer(self, operation: str):
        """开始计时"""
        with self.lock:
            self.start_times[operation] = time.time()

    def end_timer(self, operation: str, message: Optional[str] = None):
        """结束计时并记录"""
        with self.lock:
            if operation in self.start_times:
                duration = time.time() - self.start_times[operation]
                del self.start_times[operation]

                msg = message or f"操作 {operation} 完成"
                self.info(f"{msg} (耗时: {duration:.3f}秒)",
                          operation=operation, duration=duration)


class PerformanceLogger:
    """性能日志记录器"""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.performance_log = logging.getLogger('performance')
        self.performance_log.setLevel(logging.INFO)
        self.performance_log.handlers.clear()

        if log_file:
            self._setup_file_handler(log_file)

    def _setup_file_handler(self, log_file: str):
        """设置文件处理器"""
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                # 使用setattr动态添加属性
                setattr(self.performance_log, 'performance_metrics', {
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'thread_count': process.num_threads(),
                    'open_files': len(process.open_files()),
                })
            except Exception:  # nosec B110
                # 在无法获取进程信息时静默失败
                pass

        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # 创建性能格式化器
        formatter = PerformanceFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(performance_metrics)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        self.performance_log.addHandler(file_handler)

    def log(self, operation: str, duration_ms: float, success: bool, details: Optional[dict] = None):
        """记录性能日志"""
        duration_ms = duration_ms * 1000  # 转换为毫秒
        self.performance_log.info(
            f"PERF: {operation} - duration={duration_ms:.2f}ms, success={success}, details={details}")


class LogManager:
    """
    统一的日志管理器，提供线程安全的日志操作。
    """

    def __init__(self, log_file: Optional[str] = None, verbose: bool = False, is_audit: bool = False):
        self.log_file = log_file
        self.verbose = verbose
        self.is_audit = is_audit
        self.performance_logger: Optional[PerformanceLogger] = None
        self.setup_logging()

    def setup_logging(self):
        """设置日志系统"""

        # 设置基础的日志记录器
        root_logger = logging.getLogger()
        if self.verbose:
            root_logger.setLevel(logging.DEBUG)
        else:
            root_logger.setLevel(logging.INFO)

        # 清除已有的handlers
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        # 标准输出handler
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(SecureFormatter(
            '%(asctime)s - %(levelname)s - %(message)s'))
        if not self.verbose:
            stdout_handler.addFilter(lambda record: record.levelno >= logging.INFO)
        root_logger.addHandler(stdout_handler)

        # 文件输出handler
        if self.log_file:
            # 日志轮转
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8'
            )
            file_handler.setFormatter(SecureFormatter(
                '%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
            root_logger.addHandler(file_handler)

            # JSON日志输出
            json_log_file = self.log_file.replace('.log', '.json')
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8'
            )
            # 假设有一个JSONFormatter
            # json_handler.setFormatter(JSONFormatter())
            # root_logger.addHandler(json_handler)

        # 初始化性能日志记录器
        self.performance_logger = PerformanceLogger(self.log_file)

        # 审计日志
        if self.is_audit:
            audit_log_file = self.log_file.replace(
                '.log', '_audit.log') if self.log_file else 'audit.log'
            audit_handler = logging.handlers.RotatingFileHandler(
                audit_log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
            )
            audit_handler.setFormatter(logging.Formatter(
                '%(asctime)s - AUDIT - %(message)s'))
            audit_handler.setLevel(logging.INFO)

            audit_logger = logging.getLogger('audit')
            audit_logger.addHandler(audit_handler)
            audit_logger.propagate = False

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)

    def log_performance(self, operation: str, duration_ms: float, success: bool, details: Optional[dict] = None):
        if self.performance_logger:
            self.performance_logger.log(operation, duration_ms, success, details)

    def log_audit(self, message: str, level: str = "info"):
        audit_logger = logging.getLogger('audit')
        if level.lower() == "info":
            audit_logger.info(message)
        elif level.lower() == "warning":
            audit_logger.warning(message)


# 全局日志管理器实例
_log_manager_instance: Optional[LogManager] = None


def setup_logging(verbose: bool = False, log_file: Optional[str] = None):
    global _log_manager_instance
    if _log_manager_instance is None:
        _log_manager_instance = LogManager(log_file=log_file, verbose=verbose)


def get_log_manager() -> LogManager:
    """获取全局日志管理器实例，如果不存在则创建。"""
    if _log_manager_instance is None:
        setup_logging()
    # 在setup_logging之后，_log_manager_instance保证不会是None
    assert _log_manager_instance is not None  # nosec B101
    return _log_manager_instance
