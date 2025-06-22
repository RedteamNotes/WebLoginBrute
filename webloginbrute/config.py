#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import yaml
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator, ValidationError
from .exceptions import ConfigurationError

class Config(BaseModel):
    """
    统一管理所有配置项，支持命令行和YAML配置文件，基于pydantic自动类型和范围校验。
    """
    form_url: str = Field(..., description="登录表单URL")
    submit_url: str = Field(..., description="登录提交URL")
    username_file: str = Field(..., description="用户名字典文件")
    password_file: str = Field(..., description="密码字典文件")
    csrf: Optional[str] = Field(None, description="CSRF token字段名")
    login_field: Optional[str] = None
    login_value: Optional[str] = None
    cookie_file: Optional[str] = None
    timeout: int = Field(30, ge=1, le=600, description="请求超时时间（秒）")
    threads: int = Field(5, ge=1, le=100, description="并发线程数")
    resume: bool = False
    progress_file: str = Field('bruteforce_progress.json', description="进度文件路径")
    aggression_level: str = Field('A1', regex=r'^A[0-3]$', description="对抗级别")
    dry_run: bool = False
    verbose: bool = False

    @classmethod
    def from_args_and_yaml(cls):
        args = cls.parse_args()
        config_file = getattr(args, 'config_file', None)
        file_config = {}
        if config_file:
            file_config = cls.load_yaml_config(config_file)
        merged = {**file_config, **vars(args)}
        try:
            return cls.parse_obj(merged)
        except ValidationError as e:
            raise ConfigurationError(f"配置参数校验失败: {e}")

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description="WebLoginBrute 配置")
        parser.add_argument('--config-file', help='YAML配置文件路径，可选')
        parser.add_argument('--form-url', required=False, help='登录表单URL')
        parser.add_argument('--submit-url', required=False, help='登录提交URL')
        parser.add_argument('--username-file', required=False, help='用户名字典文件')
        parser.add_argument('--password-file', required=False, help='密码字典文件')
        parser.add_argument('--csrf', required=False, default=None, help='CSRF token字段名')
        parser.add_argument('--login-field', help='额外的登录字段名')
        parser.add_argument('--login-value', help='额外的登录字段值')
        parser.add_argument('--cookie-file', help='Cookie文件路径')
        parser.add_argument('--timeout', type=int, default=30, help='请求超时时间（秒）')
        parser.add_argument('--threads', type=int, default=5, help='并发线程数')
        parser.add_argument('--resume', action='store_true', help='从上次中断的地方继续')
        parser.add_argument('--progress-file', default='bruteforce_progress.json', help='进度文件路径')
        parser.add_argument('--aggression-level', choices=['A0', 'A1', 'A2', 'A3'], default='A1', help='对抗级别')
        parser.add_argument('--dry-run', action='store_true', help='测试模式，不实际发送请求')
        parser.add_argument('--verbose', action='store_true', help='详细输出')
        return parser.parse_args()

    @staticmethod
    def load_yaml_config(path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            raise ConfigurationError(f"配置文件不存在: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    @validator('form_url', 'submit_url')
    def url_must_be_http(cls, v):
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL必须以http://或https://开头')
        return v

    @validator('username_file', 'password_file')
    def file_must_exist(cls, v):
        if not os.path.exists(v):
            raise ValueError(f'文件不存在: {v}')
        return v
