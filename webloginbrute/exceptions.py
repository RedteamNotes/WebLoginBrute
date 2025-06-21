#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class BruteForceError(Exception):
    """基础异常类"""
    pass

class ConfigurationError(BruteForceError):
    """配置错误"""
    pass

class NetworkError(BruteForceError):
    """网络错误"""
    pass

class SessionError(BruteForceError):
    """会话错误"""
    pass

class ValidationError(BruteForceError):
    """验证错误"""
    pass

class SecurityError(BruteForceError):
    """安全错误"""
    pass

class RateLimitError(BruteForceError):
    """频率限制错误"""
    pass
