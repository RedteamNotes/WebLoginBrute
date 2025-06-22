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
import threading
from datetime import datetime
from logging import LogRecord
from threading import Lock
import re
from typing import Optional, Literal, Dict, Any

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# 日志主题
LOGGING_THEME = {
    "logging.level.debug": "cyan",
    "logging.level.info": "green",
    "logging.level.warning": "yellow",
    "logging.level.error": "red",
    "logging.level.critical": "bold red",
}

# 线程局部存储，用于跟踪日志来源
log_source = threading.local()
log_source.is_verbose = False
log_source.is_dry_run = False

# 敏感信息字段列表
SENSITIVE_FIELDS = [
    "password",
    "pass",
    "pwd",
    "secret",
    "token",
    "apikey",
    "privatekey",
    "sessionid",
    "cookie",
    "authorization",
]

# 敏感信息过滤的正则表达式
SENSITIVE_PATTERNS = [
    re.compile(
        r"(\b" + field + r'\b\s*[:=]\s*[\'"]?)(.*?)([\'"]?[\s,}])', re.IGNORECASE
    )
    for field in SENSITIVE_FIELDS
]

MASK = "***"


class SecureFormatter(logging.Formatter):
    """安全日志格式化器，自动过滤敏感信息"""

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: Literal["%", "{", "$"] = "%",
    ):
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
            message = pattern.sub(r"\1" + MASK + r"\3", message)

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
            log_record["timestamp"] = datetime.fromtimestamp(record.created).isoformat()

        if self.include_level:
            log_record["level"] = record.levelname

        if self.include_name:
            log_record["logger"] = record.name

        # 清理消息
        log_record["message"] = SecureFormatter()._filter_sensitive_info(
            record.getMessage()
        )

        # 添加额外字段
        if hasattr(record, "module"):
            log_record["module"] = record.module

        if hasattr(record, "funcName"):
            log_record["function"] = record.funcName

        if hasattr(record, "lineno"):
            log_record["line"] = record.lineno

        if hasattr(record, "pathname"):
            log_record["file"] = record.pathname

        # 添加异常信息
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # 添加自定义字段
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
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
        if hasattr(record, "performance_metrics"):
            with self.lock:
                if PSUTIL_AVAILABLE:
                    try:
                        process = psutil.Process()
                        # 使用setattr动态添加属性
                        setattr(
                            record,
                            "performance_metrics",
                            {
                                "cpu_percent": process.cpu_percent(),
                                "memory_mb": process.memory_info().rss / 1024 / 1024,
                                "thread_count": process.num_threads(),
                                "open_files": len(process.open_files()),
                            },
                        )
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
                extra["performance"] = {
                    "cpu_percent": process.cpu_percent(),
                    "memory_mb": process.memory_info().rss / 1024 / 1024,
                    "thread_count": process.num_threads(),
                    "open_files": len(process.open_files()),
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
                self.info(
                    f"{msg} (耗时: {duration:.3f}秒)",
                    operation=operation,
                    duration=duration,
                )


class PerformanceLogger:
    """性能日志记录器"""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.performance_log = logging.getLogger("performance")
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
                setattr(
                    self.performance_log,
                    "performance_metrics",
                    {
                        "cpu_percent": process.cpu_percent(),
                        "memory_mb": process.memory_info().rss / 1024 / 1024,
                        "thread_count": process.num_threads(),
                        "open_files": len(process.open_files()),
                    },
                )
            except Exception:  # nosec B110
                # 在无法获取进程信息时静默失败
                pass

        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # 创建性能格式化器
        formatter = PerformanceFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(performance_metrics)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)

        self.performance_log.addHandler(file_handler)

    def log(
        self,
        operation: str,
        duration_ms: float,
        success: bool,
        details: Optional[dict] = None,
    ):
        """记录性能日志"""
        duration_ms = duration_ms * 1000  # 转换为毫秒
        self.performance_log.info(
            f"PERF: {operation} - duration={duration_ms:.2f}ms, success={success}, details={details}"
        )


class LogManager:
    """
    统一的日志管理器，提供线程安全的日志操作。
    """

    def __init__(
        self,
        log_file: Optional[str] = None,
        verbose: bool = False,
        is_audit: bool = False,
    ):
        self.log_file = log_file
        self.verbose = verbose
        self.is_audit = is_audit
        self.performance_logger = PerformanceLogger(
            log_file.replace(".log", "_perf.log") if log_file else None
        )
        self.setup_logging()

    def setup_logging(self):
        """设置日志系统"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO if not self.verbose else logging.DEBUG)

        # 清除现有处理器
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        # RichHandler用于控制台输出
        console_handler = CustomRichHandler(
            console=Console(stderr=True, theme=Theme(LOGGING_THEME)),
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        console_handler.setFormatter(
            SecureFormatter("[%(asctime)s] - %(message)s", "%H:%M:%S")
        )
        root_logger.addHandler(console_handler)

        # 文件处理器
        if self.log_file:
            # 主日志文件
            main_handler = logging.handlers.RotatingFileHandler(
                self.log_file, maxBytes=10 * 1024 * 1024, backupCount=5
            )
            main_handler.setFormatter(
                SecureFormatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
            )
            root_logger.addHandler(main_handler)

            # JSON日志文件
            if self.is_audit:
                json_log_path = self.log_file.replace(".log", "_audit.json")
                logging.handlers.RotatingFileHandler(
                    json_log_path, maxBytes=5 * 1024 * 1024, backupCount=3
                )

    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器"""
        return logging.getLogger(name)

    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool,
        details: Optional[dict] = None,
    ):
        if self.performance_logger:
            self.performance_logger.log(operation, duration_ms, success, details)

    def log_audit(self, message: str, level: str = "info"):
        audit_logger = logging.getLogger("audit")
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


class CustomRichHandler(RichHandler):
    def __init__(
        self,
        console=Console(),
        show_time=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        omit_repeated_times=False,
    ):
        super().__init__(
            console=console,
            show_time=show_time,
            rich_tracebacks=rich_tracebacks,
            tracebacks_show_locals=tracebacks_show_locals,
            omit_repeated_times=omit_repeated_times,
        )

    def emit(self, record: LogRecord):
        # 在这里添加自定义的日志处理逻辑
        super().emit(record)

    def format(self, record: LogRecord) -> str:
        # 在这里添加自定义的日志格式化逻辑
        return super().format(record)
