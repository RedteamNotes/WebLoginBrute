#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebLoginBrute 增强日志系统
提供结构化日志、性能监控、日志轮转、安全过滤等功能
"""

import json
import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union, Literal
from threading import Lock
import hashlib
import re

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from . import __version__


class SecureFormatter(logging.Formatter):
    """安全日志格式化器，自动过滤敏感信息"""
    
    # 敏感字段模式
    SENSITIVE_PATTERNS = [
        r'password["\']?\s*[:=]\s*["\']?[^"\s,}]+',
        r'passwd["\']?\s*[:=]\s*["\']?[^"\s,}]+',
        r'token["\']?\s*[:=]\s*["\']?[^"\s,}]+',
        r'secret["\']?\s*[:=]\s*["\']?[^"\s,}]+',
        r'key["\']?\s*[:=]\s*["\']?[^"\s,}]+',
        r'api_key["\']?\s*[:=]\s*["\']?[^"\s,}]+',
        r'cookie["\']?\s*[:=]\s*["\']?[^"\s,}]+',
        r'session["\']?\s*[:=]\s*["\']?[^"\s,}]+',
        r'auth["\']?\s*[:=]\s*["\']?[^"\s,}]+',
        r'credential["\']?\s*[:=]\s*["\']?[^"\s,}]+',
    ]
    
    # 编译正则表达式
    SENSITIVE_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in SENSITIVE_PATTERNS]
    
    def __init__(self, fmt=None, datefmt=None, style: Literal['%', '{', '$'] = '%', mask_char='*'):
        super().__init__(fmt, datefmt, style)
        self.mask_char = mask_char
    
    @staticmethod
    def _sanitize_log_message(message: str) -> str:
        """清理日志消息中的敏感信息"""
        if not message:
            return message
        
        # 替换敏感信息
        sanitized = message
        for regex in SecureFormatter.SENSITIVE_REGEX:
            sanitized = regex.sub(r'\1***', sanitized)
        
        # 额外的安全检查
        sensitive_words = ['password', 'passwd', 'token', 'secret', 'key', 'cookie', 'session']
        for word in sensitive_words:
            if word in sanitized.lower():
                # 查找并替换敏感值
                pattern = rf'{word}["\']?\s*[:=]\s*["\']?([^"\s,}}]+)["\']?'
                sanitized = re.sub(pattern, rf'{word}="***"', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def format(self, record):
        """格式化日志记录"""
        # 清理消息
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._sanitize_log_message(record.msg)
        
        # 清理参数
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    self._sanitize_log_message(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        
        return super().format(record)


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
        log_record['message'] = SecureFormatter._sanitize_log_message(record.getMessage())
        
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
                    except Exception:
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
            except Exception:
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


class LogManager:
    """日志管理器"""
    
    def __init__(self, config=None):
        self.config = config
        self.loggers = {}
        self.handlers = {}
        self.lock = Lock()
        
        # 日志配置
        self.log_config = {
            'console_level': logging.INFO,
            'file_level': logging.DEBUG,
            'json_level': logging.INFO,
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'log_dir': 'logs',
            'enable_json': False,
            'enable_performance': False,
            'enable_rotation': True,
        }
        
        if config:
            self._update_config_from_config()
    
    def _update_config_from_config(self):
        """从配置对象更新日志配置"""
        if self.config and hasattr(self.config, 'verbose') and self.config.verbose:
            self.log_config['console_level'] = logging.DEBUG
        
        if self.config and hasattr(self.config, 'log') and self.config.log:
            self.log_config['log_dir'] = os.path.dirname(self.config.log) or 'logs'
    
    def setup_logging(self, name: str = 'webloginbrute', 
                     log_file: Optional[str] = None, 
                     json_log_file: Optional[str] = None,
                     enable_console: bool = True,
                     enable_file: bool = True,
                     enable_json: bool = False,
                     enable_performance: bool = False):
        """设置日志系统"""
        
        # 创建日志目录
        if enable_file or enable_json:
            os.makedirs(self.log_config['log_dir'], exist_ok=True)
        
        # 获取根日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 控制台处理器
        if enable_console:
            console_handler = self._create_console_handler()
            logger.addHandler(console_handler)
        
        # 文件处理器
        if enable_file and log_file:
            file_handler = self._create_file_handler(log_file)
            logger.addHandler(file_handler)
        
        # JSON文件处理器
        if enable_json and json_log_file:
            json_handler = self._create_json_handler(json_log_file)
            logger.addHandler(json_handler)
        
        # 性能监控处理器
        if enable_performance:
            perf_handler = self._create_performance_handler()
            logger.addHandler(perf_handler)
        
        # 设置结构化日志记录器
        structured_logger = StructuredLogger(name)
        self.loggers[name] = structured_logger
        
        return structured_logger
    
    def _create_console_handler(self):
        """创建控制台处理器"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.log_config['console_level'])
        
        # 创建格式化器
        formatter = SecureFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_file_handler(self, log_file: str):
        """创建文件处理器"""
        if self.log_config['enable_rotation']:
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=self.log_config['max_file_size'],
                backupCount=self.log_config['backup_count'],
                encoding='utf-8'
            )
        else:
            handler = logging.FileHandler(log_file, encoding='utf-8')
        
        handler.setLevel(self.log_config['file_level'])
        
        # 创建格式化器
        formatter = SecureFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_json_handler(self, json_log_file: str):
        """创建JSON文件处理器"""
        if self.log_config['enable_rotation']:
            handler = logging.handlers.RotatingFileHandler(
                json_log_file,
                maxBytes=self.log_config['max_file_size'],
                backupCount=self.log_config['backup_count'],
                encoding='utf-8'
            )
        else:
            handler = logging.FileHandler(json_log_file, encoding='utf-8')
        
        handler.setLevel(self.log_config['json_level'])
        
        # 创建JSON格式化器
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        
        return handler
    
    def _create_performance_handler(self):
        """创建性能监控处理器"""
        perf_file = os.path.join(self.log_config['log_dir'], 'performance.log')
        
        if self.log_config['enable_rotation']:
            handler = logging.handlers.RotatingFileHandler(
                perf_file,
                maxBytes=self.log_config['max_file_size'],
                backupCount=self.log_config['backup_count'],
                encoding='utf-8'
            )
        else:
            handler = logging.FileHandler(perf_file, encoding='utf-8')
        
        handler.setLevel(logging.INFO)
        
        # 创建性能格式化器
        formatter = PerformanceFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(performance_metrics)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def get_logger(self, name: str) -> StructuredLogger:
        """获取结构化日志记录器"""
        with self.lock:
            if name not in self.loggers:
                self.loggers[name] = StructuredLogger(name)
            return self.loggers[name]
    
    def log_performance_metrics(self, metrics: Dict[str, Any], level: str = 'info'):
        """记录性能指标"""
        logger = self.get_logger('performance')
        
        # 添加时间戳
        metrics['timestamp'] = datetime.now().isoformat()
        
        if level == 'info':
            logger.info("性能指标", **metrics)
        elif level == 'warning':
            logger.warning("性能警告", **metrics)
        elif level == 'error':
            logger.error("性能错误", **metrics)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = 'info'):
        """记录安全事件"""
        logger = self.get_logger('security')
        
        # 添加安全事件信息
        security_data = {
            'event_type': event_type,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            **details
        }
        
        if severity == 'critical':
            logger.critical(f"安全事件: {event_type}", **security_data)
        elif severity == 'error':
            logger.error(f"安全事件: {event_type}", **security_data)
        elif severity == 'warning':
            logger.warning(f"安全事件: {event_type}", **security_data)
        else:
            logger.info(f"安全事件: {event_type}", **security_data)
    
    def log_operation(self, operation: str, details: Dict[str, Any], level: str = 'info'):
        """记录操作日志"""
        logger = self.get_logger('operation')
        
        # 添加操作信息
        operation_data = {
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            **details
        }
        
        if level == 'info':
            logger.info(f"操作: {operation}", **operation_data)
        elif level == 'warning':
            logger.warning(f"操作: {operation}", **operation_data)
        elif level == 'error':
            logger.error(f"操作: {operation}", **operation_data)
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        import glob
        from datetime import datetime, timedelta
        
        log_dir = self.log_config['log_dir']
        if not os.path.exists(log_dir):
            return
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 查找所有日志文件
        log_patterns = [
            os.path.join(log_dir, '*.log'),
            os.path.join(log_dir, '*.log.*'),
        ]
        
        for pattern in log_patterns:
            for log_file in glob.glob(pattern):
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                    if file_time < cutoff_date:
                        os.remove(log_file)
                        print(f"已删除旧日志文件: {log_file}")
                except Exception as e:
                    print(f"删除日志文件失败 {log_file}: {e}")


# 全局日志管理器
_log_manager = None


def get_log_manager(config=None) -> LogManager:
    """获取全局日志管理器"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager(config)
    return _log_manager


def setup_logging(verbose: bool = False, 
                 log_file: Optional[str] = None,
                 json_log_file: Optional[str] = None,
                 enable_json: bool = False,
                 enable_performance: bool = False,
                 config=None):
    """设置日志系统的便捷函数"""
    
    # 创建日志管理器
    log_manager = get_log_manager(config)
    
    # 确定日志文件路径
    if log_file is None and config and hasattr(config, 'log') and config.log:
        log_file = config.log
    
    if json_log_file is None and enable_json:
        json_log_file = os.path.join('logs', 'webloginbrute.json')
    
    # 设置日志
    structured_logger = log_manager.setup_logging(
        name='webloginbrute',
        log_file=log_file,
        json_log_file=json_log_file,
        enable_console=True,
        enable_file=log_file is not None,
        enable_json=enable_json,
        enable_performance=enable_performance
    )
    
    # 设置根日志记录器级别
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    return structured_logger


def log_performance(metrics: Dict[str, Any], level: str = 'info'):
    """记录性能指标的便捷函数"""
    log_manager = get_log_manager()
    log_manager.log_performance_metrics(metrics, level)


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = 'info'):
    """记录安全事件的便捷函数"""
    log_manager = get_log_manager()
    log_manager.log_security_event(event_type, details, severity)


def log_operation(operation: str, details: Dict[str, Any], level: str = 'info'):
    """记录操作的便捷函数"""
    log_manager = get_log_manager()
    log_manager.log_operation(operation, details, level)
