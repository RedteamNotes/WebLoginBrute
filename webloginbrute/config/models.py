#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from typing import Any, Dict, Optional, List
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
)

from ..utils.exceptions import SecurityError
from ..version import __version__

# 使用统一的版本管理
version = __version__


# 环境变量配置
def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """安全地获取环境变量"""
    return os.environ.get(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """获取布尔环境变量"""
    value = get_env_var(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int = 0) -> int:
    """获取整数环境变量"""
    value = get_env_var(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_env_float(key: str, default: float = 0.0) -> float:
    """获取浮点数环境变量"""
    value = get_env_var(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


class Config(BaseModel):
    """
    统一管理所有配置项，基于pydantic自动类型和范围校验。
    """

    url: str = Field(..., description="登录表单页面URL")
    action: str = Field(..., description="登录表单提交URL")
    users: str = Field(..., description="用户名字典文件路径")
    passwords: str = Field(..., description="密码字典文件路径")

    # 可选配置
    csrf: Optional[str] = Field(None, description="CSRF token字段名")
    login_field: Optional[str] = Field(None, description="额外的登录字段名")
    login_value: Optional[str] = Field(None, description="额外的登录字段值")
    cookie: Optional[str] = Field(None, description="Cookie文件路径")
    config: Optional[str] = Field(None, description="YAML配置文件路径", exclude=True)

    # 性能配置
    timeout: int = Field(
        default_factory=lambda: get_env_int("WEBLOGINBRUTE_TIMEOUT", 30),
        ge=1,
        le=300,
        description="请求超时时间（秒）",
    )
    threads: int = Field(
        default_factory=lambda: get_env_int("WEBLOGINBRUTE_THREADS", 5),
        ge=1,
        le=100,
        description="并发线程数",
    )

    # 内存管理配置
    max_memory_mb: int = Field(
        default_factory=lambda: get_env_int("WEBLOGINBRUTE_MAX_MEMORY_MB", 1024),
        ge=128,
        le=8192,
        description="最大内存使用量(MB)",
    )
    memory_warning_threshold: int = Field(
        default_factory=lambda: get_env_int(
            "WEBLOGINBRUTE_MEMORY_WARNING_THRESHOLD", 80
        ),
        ge=50,
        le=95,
        description="内存警告阈值(%)",
    )
    memory_critical_threshold: int = Field(
        default_factory=lambda: get_env_int(
            "WEBLOGINBRUTE_MEMORY_CRITICAL_THRESHOLD", 95
        ),
        ge=80,
        le=99,
        description="内存临界阈值(%)",
    )
    memory_cleanup_interval: int = Field(
        default_factory=lambda: get_env_int(
            "WEBLOGINBRUTE_MEMORY_CLEANUP_INTERVAL", 60
        ),
        ge=10,
        le=300,
        description="内存清理间隔(秒)",
    )

    # 会话管理配置
    session_rotation_interval: int = Field(
        default_factory=lambda: get_env_int(
            "WEBLOGINBRUTE_SESSION_ROTATION_INTERVAL", 300
        ),
        ge=60,
        le=3600,
        description="会话轮换间隔(秒)",
    )
    session_lifetime: int = Field(
        default_factory=lambda: get_env_int("WEBLOGINBRUTE_SESSION_LIFETIME", 1800),
        ge=300,
        le=7200,
        description="会话生命周期(秒)",
    )
    max_session_pool_size: int = Field(
        default_factory=lambda: get_env_int("WEBLOGINBRUTE_MAX_SESSION_POOL_SIZE", 50),
        ge=10,
        le=200,
        description="最大会话池大小",
    )
    enable_session_rotation: bool = Field(
        default_factory=lambda: get_env_bool(
            "WEBLOGINBRUTE_ENABLE_SESSION_ROTATION", True
        ),
        description="启用会话轮换",
    )
    rotation_strategy: str = Field(
        default_factory=lambda: get_env_var("WEBLOGINBRUTE_ROTATION_STRATEGY")
        or "time",
        description="轮换策略",
    )

    # 健康检查配置
    enable_health_check: bool = Field(
        default_factory=lambda: get_env_bool("WEBLOGINBRUTE_ENABLE_HEALTH_CHECK", True),
        description="启用健康检查",
    )
    validate_network_connectivity: bool = Field(
        default_factory=lambda: get_env_bool(
            "WEBLOGINBRUTE_ENABLE_NETWORK_VALIDATION", True
        ),
        description="验证网络连通性",
    )
    validate_file_integrity: bool = Field(
        default_factory=lambda: get_env_bool(
            "WEBLOGINBRUTE_ENABLE_FILE_VALIDATION", True
        ),
        description="验证文件完整性",
    )
    max_file_size: int = Field(
        default_factory=lambda: get_env_int("WEBLOGINBRUTE_MAX_FILE_SIZE", 100),
        ge=1,
        le=1000,
        description="最大文件大小(MB)",
    )

    # 安全配置
    security_level: str = Field(
        default_factory=lambda: get_env_var("WEBLOGINBRUTE_SECURITY_LEVEL")
        or "standard",
        description="安全级别",
    )
    allowed_domains: List[str] = Field(
        default_factory=list, description="允许的域名列表"
    )
    blocked_domains: List[str] = Field(
        default_factory=list, description="阻止的域名列表"
    )

    # 操作配置
    resume: bool = Field(False, description="从上次中断的地方继续")
    log: Optional[str] = Field(None, description="进度文件路径")
    aggressive: int = Field(
        default_factory=lambda: get_env_int("WEBLOGINBRUTE_AGGRESSIVE_LEVEL", 1),
        ge=0,
        le=3,
        description="对抗级别: 0(静默) 1(标准) 2(激进) 3(极限)",
    )
    dry_run: bool = Field(False, description="测试模式，不实际发送请求")
    verbose: bool = Field(
        default_factory=lambda: get_env_bool("WEBLOGINBRUTE_VERBOSE", False),
        description="详细输出",
    )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        use_enum_values=True,
    )

    @field_validator("url", "action", mode="before")
    def url_must_be_http(cls, v):
        """验证URL必须是HTTP/HTTPS"""
        if not v:
            return v
        parsed = urlparse(v)
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("URL必须使用http://或https://协议")
        return v

    @field_validator("users", "passwords", mode="before")
    def required_file_must_exist(cls, v):
        """验证必需的文件是否存在"""
        if not v:
            return v
        if not os.path.exists(v):
            raise ValueError(f"文件不存在: {v}")
        if not os.path.isfile(v):
            raise ValueError(f"路径不是一个文件: {v}")
        if not os.access(v, os.R_OK):
            raise ValueError(f"文件不可读: {v}")
        return v

    @field_validator("cookie", mode="before")
    def optional_file_must_exist_if_provided(cls, v):
        """如果提供了可选文件，验证它是否存在"""
        if not v:
            return None
        if not os.path.exists(v):
            raise ValueError(f"Cookie文件不存在: {v}")
        return v

    @field_validator("login_field", "login_value", mode="before")
    def login_field_value_length(cls, v):
        """验证登录字段值的长度"""
        if v and len(v) > 1024:
            raise ValueError("登录字段值过长")
        return v

    @field_validator("csrf", mode="before")
    def csrf_length(cls, v):
        """验证CSRF token字段名的长度"""
        if v and len(v) > 256:
            raise ValueError("CSRF token字段名过长")
        return v

    @field_validator("rotation_strategy")
    def validate_rotation_strategy(cls, v):
        """验证轮换策略是否有效"""
        valid_strategies = {"time", "requests", "failure"}
        if v not in valid_strategies:
            raise ValueError(f"无效的轮换策略: {v}")
        return v

    @field_validator("security_level")
    def validate_security_level(cls, v):
        """验证安全级别是否有效"""
        valid_levels = {"none", "standard", "high", "paranoid"}
        if v not in valid_levels:
            raise ValueError(f"无效的安全级别: {v}")
        return v

    @model_validator(mode="after")
    def validate_config_consistency(self):
        """验证配置项之间的一致性"""
        # 验证域名白名单
        if self.allowed_domains:
            url_domain = urlparse(self.url).hostname
            action_domain = urlparse(self.action).hostname
            if url_domain not in self.allowed_domains:
                raise SecurityError(
                    f"目标URL域名 '{url_domain}' 不在允许的域名列表中",
                    security_check="allowed_domains",
                )
            if action_domain not in self.allowed_domains:
                raise SecurityError(
                    f"Action URL域名 '{action_domain}' 不在允许的域名列表中",
                    security_check="allowed_domains",
                )

        # 验证内存阈值
        if self.memory_critical_threshold <= self.memory_warning_threshold:
            raise ValueError("内存临界阈值必须高于警告阈值")

        return self

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要，用于报告"""
        return self.model_dump(exclude={"users", "passwords", "cookie"}) 