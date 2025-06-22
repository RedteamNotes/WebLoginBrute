#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import yaml
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator, ValidationError
from .exceptions import ConfigurationError
from .version import __version__, get_version_info

# 使用统一的版本管理
version = __version__

class Config(BaseModel):
    """
    统一管理所有配置项，支持命令行和YAML配置文件，基于pydantic自动类型和范围校验。
    """
    url: str = Field(..., description="登录表单页面URL")
    action: str = Field(..., description="登录表单提交URL")
    users: str = Field(..., description="用户名字典文件")
    passwords: str = Field(..., description="密码字典文件")
    csrf: Optional[str] = Field(None, description="CSRF token字段名")
    login_field: Optional[str] = None
    login_value: Optional[str] = None
    cookie: Optional[str] = None
    timeout: int = Field(30, ge=1, le=600, description="请求超时时间（秒）")
    threads: int = Field(5, ge=1, le=100, description="并发线程数")
    resume: bool = False
    log: str = Field('bruteforce_progress.json', description="进度文件路径")
    aggressive: int = Field(1, ge=0, le=3, description="对抗级别: 0(静默) 1(标准) 2(激进) 3(极限)")
    dry_run: bool = False
    verbose: bool = False
    
    # 内存管理配置
    max_memory_mb: int = Field(500, ge=100, le=2000, description="最大内存使用量(MB)")
    memory_warning_threshold: float = Field(0.8, ge=0.5, le=0.95, description="内存警告阈值")
    memory_critical_threshold: float = Field(0.9, ge=0.7, le=0.99, description="内存临界阈值")
    memory_cleanup_interval: int = Field(60, ge=30, le=300, description="内存清理间隔(秒)")
    
    # 会话管理配置
    session_rotation_interval: int = Field(300, ge=60, le=1800, description="会话轮换间隔(秒)")
    session_lifetime: int = Field(600, ge=300, le=3600, description="会话生命周期(秒)")
    max_session_pool_size: int = Field(100, ge=10, le=500, description="最大会话池大小")
    enable_session_rotation: bool = Field(True, description="是否启用会话轮换")
    rotation_strategy: str = Field("time", description="轮换策略")

    @classmethod
    def from_args_and_yaml(cls) -> 'Config':
        args, defaults = cls.parse_args()
        config_path = args.config
        file_config = {}
        if config_path:
            if not os.path.exists(config_path):
                raise ConfigurationError(f"配置文件不存在: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f) or {}
        final_config = file_config.copy()
        for key, value in vars(args).items():
            if key != 'config' and value is not None and value != defaults.get(key):
                final_config[key] = value
        try:
            config = cls.parse_obj(final_config)
            import logging
            logging.debug(f"最终生效配置: {config.dict()}")
            return config
        except ValidationError as e:
            raise ConfigurationError(f"配置参数校验失败: {e}")

    @staticmethod
    def parse_args() -> tuple:
        parser = argparse.ArgumentParser(description="WebLoginBrute 配置")
        parser.add_argument('--config', help='YAML配置文件路径，可选')
        parser.add_argument('-u', '--url', help='登录表单页面URL')
        parser.add_argument('-a', '--action', help='登录表单提交URL')
        parser.add_argument('-U', '--users', help='用户名字典文件')
        parser.add_argument('-P', '--passwords', help='密码字典文件')
        parser.add_argument('-s', '--csrf', help='CSRF token字段名')
        parser.add_argument('-f', '--login-field', help='额外的登录字段名')
        parser.add_argument('-v', '--login-value', help='额外的登录字段值')
        parser.add_argument('-c', '--cookie', help='Cookie文件路径')
        parser.add_argument('-T', '--timeout', type=int, help='请求超时时间（秒）')
        parser.add_argument('-t', '--threads', type=int, help='并发线程数')
        parser.add_argument('-r', '--resume', action='store_true', help='从上次中断的地方继续')
        parser.add_argument('-l', '--log', help='进度文件路径')
        parser.add_argument('-A', '--aggressive', type=int, choices=[0, 1, 2, 3], help='对抗级别: 0(静默) 1(标准) 2(激进) 3(极限)')
        parser.add_argument('--dry-run', action='store_true', help='测试模式，不实际发送请求')
        parser.add_argument('--verbose', action='store_true', help='详细输出')
        parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {version}')
        
        # 内存管理参数
        parser.add_argument('--max-memory', type=int, help='最大内存使用量(MB)')
        parser.add_argument('--memory-warning-threshold', type=float, help='内存警告阈值')
        parser.add_argument('--memory-critical-threshold', type=float, help='内存临界阈值')
        parser.add_argument('--memory-cleanup-interval', type=int, help='内存清理间隔(秒)')
        
        # 会话管理参数
        parser.add_argument('--session-rotation-interval', type=int, help='会话轮换间隔(秒)')
        parser.add_argument('--session-lifetime', type=int, help='会话生命周期(秒)')
        parser.add_argument('--max-session-pool-size', type=int, help='最大会话池大小')
        parser.add_argument('--disable-session-rotation', action='store_true', help='禁用会话轮换')
        parser.add_argument('--rotation-strategy', choices=['time', 'request_count', 'error_rate'], help='轮换策略')
        
        # 参数别名映射，提升兼容性
        parser.add_argument('--form-url', dest='url', help='登录表单页面URL (别名)')
        parser.add_argument('--submit-url', dest='action', help='登录表单提交URL (别名)')
        parser.add_argument('--username-file', dest='users', help='用户名字典文件 (别名)')
        parser.add_argument('--password-file', dest='passwords', help='密码字典文件 (别名)')
        parser.add_argument('--csrf-field', dest='csrf', help='CSRF token字段名 (别名)')
        parser.add_argument('--cookie-file', dest='cookie', help='Cookie文件路径 (别名)')
        parser.add_argument('--progress-file', dest='log', help='进度文件路径 (别名)')
        parser.add_argument('--aggression-level', dest='aggressive', type=int, choices=[0, 1, 2, 3], help='对抗级别: 0(静默) 1(标准) 2(激进) 3(极限) (别名)')
        
        defaults = {opt.dest: opt.default for opt in parser._actions}
        args = parser.parse_args()
        
        # 处理禁用会话轮换的参数
        if args.disable_session_rotation:
            args.enable_session_rotation = False
        
        return args, defaults

    @validator('url', 'action', pre=True, always=True)
    def url_must_be_http(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL必须以http://或https://开头')
        if v and len(v) > 2048:
            raise ValueError('URL过长')
        return v

    @validator('users', 'passwords', pre=True, always=True)
    def required_file_must_exist(cls, v):
        if v and not os.path.exists(v):
            raise ValueError(f'必需文件不存在: {v}')
        if v and len(v) > 256:
            raise ValueError('文件路径过长')
        return v

    @validator('cookie', pre=True, always=True)
    def optional_file_must_exist_if_provided(cls, v):
        if v and not os.path.exists(v):
            raise ValueError(f'可选文件不存在: {v}')
        if v and len(v) > 256:
            raise ValueError('文件路径过长')
        return v

    @validator('login_field', 'login_value', pre=True, always=True)
    def login_field_value_length(cls, v):
        if v and len(v) > 128:
            raise ValueError('字段值过长')
        return v

    @validator('csrf', pre=True, always=True)
    def csrf_length(cls, v):
        if v and len(v) > 128:
            raise ValueError('CSRF字段名过长')
        return v
