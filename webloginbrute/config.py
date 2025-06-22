#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, validator

from .exceptions import ConfigurationError


class Config(BaseModel):
    """
    统一管理所有配置项，支持命令行和YAML配置文件，基于pydantic自动类型和范围校验。
    """

    form: str = Field(..., description="登录表单URL")
    submit: str = Field(..., description="登录提交URL")
    users: str = Field(..., description="用户名字典文件")
    passwords: str = Field(..., description="密码字典文件")
    csrf: Optional[str] = Field(None, description="CSRF token字段名")
    field: Optional[str] = None
    value: Optional[str] = None
    cookies: Optional[str] = None
    timeout: int = Field(30, ge=1, le=600, description="请求超时时间（秒）")
    threads: int = Field(5, ge=1, le=100, description="并发线程数")
    resume: bool = False
    progress: str = Field("bruteforce_progress.json", description="进度文件路径")
    level: str = Field("A1", regex=r"^A[0-3]$", description="对抗级别")
    dry_run: bool = False
    verbose: bool = False

    @classmethod
    def from_args_and_yaml(cls):
        # 1. 解析命令行参数，不设默认值，以便判断用户是否显式提供
        args, defaults = cls.parse_args()

        # 2. 如果提供了配置文件，加载它
        config_path = args.config
        file_config = {}
        if config_path:
            if not os.path.exists(config_path):
                raise ConfigurationError(f"配置文件不存在: {config_path}")
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}

        # 3. 合并配置: file_config是基础，然后用用户在命令行提供的非默认值覆盖
        final_config = file_config.copy()
        for key, value in vars(args).items():
            if key != "config" and value is not None and value != defaults.get(key):
                final_config[key] = value

        # 4. 使用Pydantic进行最终的校验和实例化
        try:
            return cls.parse_obj(final_config)
        except ValidationError as e:
            raise ConfigurationError(f"配置参数校验失败: {e}")

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description="WebLoginBrute 配置")
        parser.add_argument("--config", help="YAML配置文件路径，可选")

        # 所有其他参数的默认值都由Pydantic模型定义，这里不再设置
        parser.add_argument("--form", help="登录表单URL")
        parser.add_argument("--submit", help="登录提交URL")
        parser.add_argument("--users", help="用户名字典文件")
        parser.add_argument("--passwords", help="密码字典文件")
        parser.add_argument("--csrf", help="CSRF token字段名")
        parser.add_argument("--field", help="额外的登录字段名")
        parser.add_argument("--value", help="额外的登录字段值")
        parser.add_argument("--cookies", help="Cookie文件路径")
        parser.add_argument("--timeout", type=int, help="请求超时时间（秒）")
        parser.add_argument("--threads", type=int, help="并发线程数")
        parser.add_argument(
            "--resume", action="store_true", help="从上次中断的地方继续"
        )
        parser.add_argument("--progress", help="进度文件路径")
        parser.add_argument(
            "--level", choices=["A0", "A1", "A2", "A3"], help="对抗级别"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="测试模式，不实际发送请求"
        )
        parser.add_argument("--verbose", action="store_true", help="详细输出")

        defaults = {opt.dest: opt.default for opt in parser._actions}
        args = parser.parse_args()
        return args, defaults

    @validator("form", "submit", pre=True, always=True)
    def url_must_be_http(cls, v):
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL必须以http://或https://开头")
        return v

    @validator("users", "passwords", "cookies", pre=True, always=True)
    def file_must_exist(cls, v):
        if v and not os.path.exists(v):
            raise ValueError(f"文件不存在: {v}")
        return v
