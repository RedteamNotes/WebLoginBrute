#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import yaml
from typing import Any, Dict
from .exceptions import ConfigurationError

class Config:
    """
    统一管理所有配置项，支持命令行和YAML配置文件。
    """
    # 显式声明所有主要配置项
    form_url: str
    submit_url: str
    username_file: str
    password_file: str
    csrf: str | None
    login_field: str | None
    login_value: str | None
    cookie_file: str | None
    timeout: int
    threads: int
    resume: bool
    progress_file: str
    aggression_level: str
    dry_run: bool
    verbose: bool

    def __init__(self):
        # 1. 解析命令行参数
        args = self.parse_args()
        config_file = getattr(args, 'config_file', None)
        file_config = {}
        if config_file:
            file_config = self.load_yaml_config(config_file)
        
        # 2. 合并配置，命令行优先
        merged = {**file_config, **vars(args)}
        # 显式赋值
        self.form_url = merged.get('form_url') or ""
        self.submit_url = merged.get('submit_url') or ""
        self.username_file = merged.get('username_file') or ""
        self.password_file = merged.get('password_file') or ""
        self.csrf = merged.get('csrf')
        self.login_field = merged.get('login_field')
        self.login_value = merged.get('login_value')
        self.cookie_file = merged.get('cookie_file')
        self.timeout = merged.get('timeout', 30)
        self.threads = merged.get('threads', 5)
        self.resume = merged.get('resume', False)
        self.progress_file = merged.get('progress_file', 'bruteforce_progress.json')
        self.aggression_level = merged.get('aggression_level', 'A1')
        self.dry_run = merged.get('dry_run', False)
        self.verbose = merged.get('verbose', False)
        # 3. 校验配置
        self.validate()

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

    def validate(self):
        # 检查必需项
        required = ['form_url', 'submit_url', 'username_file', 'password_file']
        for key in required:
            if not hasattr(self, key) or not getattr(self, key):
                raise ConfigurationError(f"缺少必需配置项: {key}")
        # 检查文件存在性
        if not os.path.exists(self.username_file):
            raise ConfigurationError(f"用户名文件不存在: {self.username_file}")
        if not os.path.exists(self.password_file):
            raise ConfigurationError(f"密码文件不存在: {self.password_file}")
        # 检查URL格式
        if not (self.form_url.startswith('http://') or self.form_url.startswith('https://')):
            raise ConfigurationError(f"表单URL格式不正确: {self.form_url}")
        if not (self.submit_url.startswith('http://') or self.submit_url.startswith('https://')):
            raise ConfigurationError(f"提交URL格式不正确: {self.submit_url}")
