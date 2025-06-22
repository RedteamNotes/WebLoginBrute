#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import traceback
from typing import Optional, Dict, Any, List
from datetime import datetime


class BruteForceError(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, 
                 error_code: Optional[str] = None, severity: str = "ERROR"):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.error_code = error_code
        self.severity = severity
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于日志记录和错误报告"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context,
            'traceback': self.traceback
        }
    
    def __str__(self) -> str:
        context_str = f" (Context: {self.context})" if self.context else ""
        code_str = f" [{self.error_code}]" if self.error_code else ""
        return f"{self.message}{code_str}{context_str}"


class ConfigurationError(BruteForceError):
    """配置错误"""
    
    def __init__(self, message: str, config_path: Optional[str] = None, 
                 invalid_fields: Optional[List[str]] = None):
        context = {
            'config_path': config_path,
            'invalid_fields': invalid_fields or []
        }
        super().__init__(message, context, "CONFIG_ERROR", "ERROR")


class NetworkError(BruteForceError):
    """网络错误"""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 status_code: Optional[int] = None, retry_count: int = 0):
        context = {
            'url': url,
            'status_code': status_code,
            'retry_count': retry_count
        }
        super().__init__(message, context, "NETWORK_ERROR", "ERROR")


class SessionError(BruteForceError):
    """会话错误"""
    
    def __init__(self, message: str, session_id: Optional[str] = None, 
                 session_age: Optional[float] = None):
        context = {
            'session_id': session_id,
            'session_age': session_age
        }
        super().__init__(message, context, "SESSION_ERROR", "WARNING")


class ValidationError(BruteForceError):
    """验证错误"""
    
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 field_value: Optional[str] = None, validation_rule: Optional[str] = None):
        context = {
            'field_name': field_name,
            'field_value': field_value,
            'validation_rule': validation_rule
        }
        super().__init__(message, context, "VALIDATION_ERROR", "ERROR")


class SecurityError(BruteForceError):
    """安全错误"""
    
    def __init__(self, message: str, security_check: Optional[str] = None, 
                 threat_level: str = "MEDIUM"):
        context = {
            'security_check': security_check,
            'threat_level': threat_level
        }
        super().__init__(message, context, "SECURITY_ERROR", "CRITICAL")


class RateLimitError(BruteForceError):
    """频率限制错误"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, 
                 rate_limit_info: Optional[Dict[str, Any]] = None):
        context = {
            'retry_after': retry_after,
            'rate_limit_info': rate_limit_info or {}
        }
        super().__init__(message, context, "RATE_LIMIT_ERROR", "WARNING")


class FileError(BruteForceError):
    """文件操作错误"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 operation: Optional[str] = None, file_size: Optional[int] = None):
        context = {
            'file_path': file_path,
            'operation': operation,
            'file_size': file_size
        }
        super().__init__(message, context, "FILE_ERROR", "ERROR")


class EncodingError(BruteForceError):
    """编码错误"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 attempted_encodings: Optional[List[str]] = None):
        context = {
            'file_path': file_path,
            'attempted_encodings': attempted_encodings or []
        }
        super().__init__(message, context, "ENCODING_ERROR", "ERROR")


class TimeoutError(BruteForceError):
    """超时错误"""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None, 
                 operation: Optional[str] = None):
        context = {
            'timeout_duration': timeout_duration,
            'operation': operation
        }
        super().__init__(message, context, "TIMEOUT_ERROR", "WARNING")


class MemoryError(BruteForceError):
    """内存错误"""
    
    def __init__(self, message: str, current_memory: Optional[float] = None, 
                 memory_limit: Optional[float] = None, memory_usage_percent: Optional[float] = None):
        context = {
            'current_memory': current_memory,
            'memory_limit': memory_limit,
            'memory_usage_percent': memory_usage_percent
        }
        super().__init__(message, context, "MEMORY_ERROR", "CRITICAL")


class ResourceError(BruteForceError):
    """资源错误"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, 
                 resource_id: Optional[str] = None, resource_usage: Optional[Dict[str, Any]] = None):
        context = {
            'resource_type': resource_type,
            'resource_id': resource_id,
            'resource_usage': resource_usage or {}
        }
        super().__init__(message, context, "RESOURCE_ERROR", "ERROR")


class HealthCheckError(BruteForceError):
    """健康检查错误"""
    
    def __init__(self, message: str, check_name: Optional[str] = None, 
                 check_result: Optional[Dict[str, Any]] = None, component: Optional[str] = None):
        context = {
            'check_name': check_name,
            'check_result': check_result or {},
            'component': component
        }
        super().__init__(message, context, "HEALTH_CHECK_ERROR", "WARNING")


class PerformanceError(BruteForceError):
    """性能错误"""
    
    def __init__(self, message: str, metric_name: Optional[str] = None, 
                 current_value: Optional[float] = None, threshold: Optional[float] = None):
        context = {
            'metric_name': metric_name,
            'current_value': current_value,
            'threshold': threshold
        }
        super().__init__(message, context, "PERFORMANCE_ERROR", "WARNING")


# 错误代码映射
ERROR_CODES = {
    'CONFIG_ERROR': '配置错误',
    'NETWORK_ERROR': '网络错误',
    'SESSION_ERROR': '会话错误',
    'VALIDATION_ERROR': '验证错误',
    'SECURITY_ERROR': '安全错误',
    'RATE_LIMIT_ERROR': '频率限制错误',
    'FILE_ERROR': '文件操作错误',
    'ENCODING_ERROR': '编码错误',
    'TIMEOUT_ERROR': '超时错误',
    'MEMORY_ERROR': '内存错误',
    'RESOURCE_ERROR': '资源错误',
    'HEALTH_CHECK_ERROR': '健康检查错误',
    'PERFORMANCE_ERROR': '性能错误'
}


def get_error_description(error_code: str) -> str:
    """获取错误代码的中文描述"""
    return ERROR_CODES.get(error_code, '未知错误')


def format_error_report(error: BruteForceError) -> str:
    """格式化错误报告"""
    error_dict = error.to_dict()
    
    report = f"""
错误报告
========
错误类型: {error_dict['error_type']}
错误代码: {error_dict['error_code']} ({get_error_description(error_dict['error_code'])})
严重程度: {error_dict['severity']}
发生时间: {error_dict['timestamp']}
错误信息: {error_dict['message']}

上下文信息:
"""
    
    for key, value in error_dict['context'].items():
        if value is not None:
            report += f"  {key}: {value}\n"
    
    if error_dict['traceback']:
        report += f"\n堆栈跟踪:\n{error_dict['traceback']}"
    
    return report
