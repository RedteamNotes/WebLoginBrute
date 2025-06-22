#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import yaml
from typing import Tuple

from .models import Config
from ..utils.exceptions import ConfigurationError
from ..services.health_check import run_health_checks


def from_args_and_yaml() -> Config:
    """
    从命令行参数和YAML配置文件创建并验证配置对象。
    这是获取配置的主要入口点。
    """
    args, defaults = parse_args()
    config_path = args.config
    file_config = {}

    if config_path:
        if not os.path.exists(config_path):
            raise ConfigurationError(
                f"配置文件不存在: {config_path}", config_path=config_path
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"YAML配置文件格式错误: {e}", config_path=config_path
            )
        except Exception as e:
            raise ConfigurationError(
                f"读取配置文件失败: {e}", config_path=config_path
            )

    # 合并配置：文件配置覆盖默认值，命令行参数覆盖文件配置
    final_config = file_config.copy()
    for key, value in vars(args).items():
        if value is not None and value != defaults.get(key):
            final_config[key] = value
    
    # 移除'config'键，因为它不是Config模型的一部分
    final_config.pop('config', None)

    try:
        config = Config.model_validate(final_config)

        # 执行初始健康检查
        if not config.dry_run and config.enable_health_check:
            run_health_checks(config)
        
        return config

    except Exception as e:
        # 捕获Pydantic验证错误和其他潜在错误
        raise ConfigurationError(f"配置验证失败: {e}")


def parse_args() -> Tuple[argparse.Namespace, dict]:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Web Login Bruteforcer",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # 创建参数组
    required = parser.add_argument_group("Required Arguments")
    optional = parser.add_argument_group("Optional Arguments")
    performance = parser.add_argument_group("Performance Tuning")
    operation = parser.add_argument_group("Operation Control")

    # 添加参数
    parser.add_argument(
        "-c", "--config", help="YAML配置文件路径"
    )

    required.add_argument("-u", "--url", help="登录页面URL")
    required.add_argument("-a", "--action", help="表单提交URL")
    required.add_argument("--users", help="用户名字典文件路径")
    required.add_argument("-p", "--passwords", help="密码字典文件路径")

    optional.add_argument("--csrf", help="CSRF Token字段名")
    optional.add_argument("--login-field", dest="login_field", help="额外的登录字段名")
    optional.add_argument("--login-value", dest="login_value", help="额外的登录字段值")
    optional.add_argument("--cookie", help="Cookie文件路径")

    performance.add_argument("-t", "--threads", type=int, help="并发线程数")
    performance.add_argument("--timeout", type=int, help="请求超时时间（秒）")
    performance.add_argument(
        "--aggressive",
        type=int,
        help="对抗级别: 0(静默) 1(标准) 2(激进) 3(极限)",
    )

    operation.add_argument("--resume", action="store_true", help="从上次中断的地方继续")
    operation.add_argument("-l", "--log", help="进度文件路径")
    operation.add_argument("--dry-run", dest="dry_run", action="store_true", help="测试模式，不实际发送请求")
    operation.add_argument("-v", "--verbose", action="store_true", help="详细输出")

    # 获取所有已定义参数的默认值
    defaults = {
        action.dest: action.default
        for action in parser._actions
        if action.default is not argparse.SUPPRESS
    }

    return parser.parse_args(), defaults 