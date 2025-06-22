#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import re
from datetime import datetime
from logging.handlers import RotatingFileHandler

from . import __version__


class SecureFormatter(logging.Formatter):
    """
    安全日志格式化程序，自动对敏感信息进行脱敏处理。
    """

    def format(self, record):
        # 复制一份消息和参数，避免修改原始记录
        msg = record.getMessage()

        # 脱敏日志消息
        msg = self._sanitize_log_message(msg)

        # 创建一个新的LogRecord进行格式化
        # 这可以避免修改原始的record对象，从而防止潜在的副作用
        safe_record = logging.LogRecord(
            record.name,
            record.levelno,
            record.pathname,
            record.lineno,
            msg,
            record.args,
            record.exc_info,
            record.funcName,
            record.stack_info,
        )

        return super().format(safe_record)

    def _sanitize_log_message(self, message: str) -> str:
        """脱敏日志消息中的敏感内容"""
        if not isinstance(message, str):
            return message

        # 脱敏用户名和密码的模式
        # 增加对不同格式的兼容性，如 "user:pass", "user/pass"
        patterns = [
            (r'(user(?:name)?\s*[:=/]?\s*[\'"]?)([^\s\'",]+)([\'"]?)', r"\1***\3"),
            (r'(pass(?:word)?\s*[:=/]?\s*[\'"]?)([^\s\'",]+)([\'"]?)', r"\1***\3"),
            (r"尝试登录[：:]\s*([^:]+):([^\s]+)", r"尝试登录: ***:***"),
            (r"登录成功[：:]\s*([^:]+):([^\s]+)", r"登录成功: ***:***"),
            (r"尝试\s*([^:]+):([^\s]+)", r"尝试 ***:***"),
        ]

        for pattern, replacement in patterns:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

        # 脱敏常见敏感字段
        message = re.sub(r'(password|token|cookie|secret|key)=\S+', r'\1=***', message, flags=re.I)

        return message


def setup_logging(verbose: bool = False):
    """
    配置日志记录器。

    该函数会设置一个根日志记录器和审计日志记录器。
    - 根记录器有两个处理器：
      1. 控制台处理器：默认只显示INFO及以上级别，verbose模式下显示DEBUG级别。
      2. 轮转文件处理器：记录所有DEBUG及以上级别的日志到文件中。
    - 审计记录器有一个独立的轮转文件处理器，用于记录安全相关的审计事件。

    Args:
        verbose (bool): 是否启用详细模式。
    """
    # 1. 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 2. 获取并配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # 清除任何可能存在的旧处理器，避免重复记录
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 3. 创建格式化器
    formatter = SecureFormatter("%(asctime)s - %(levelname)s - %(message)s")

    # 4. 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_level = logging.DEBUG if verbose else logging.INFO
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 5. 创建主日志文件的轮转处理器
    log_file = os.path.join(log_dir, f"webloginbrute_{timestamp}.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 6. 创建并配置审计日志记录器
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False  # 防止审计日志向根记录器传播，导致重复输出

    # 清除旧的审计处理器
    for handler in audit_logger.handlers[:]:
        audit_logger.removeHandler(handler)

    audit_file = os.path.join(log_dir, f"audit_{timestamp}.log")
    audit_handler = RotatingFileHandler(
        audit_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"  # 5MB
    )
    audit_handler.setFormatter(formatter)
    audit_logger.addHandler(audit_handler)

    # 7. 记录启动信息
    logging.info(f"WebLoginBrute v{__version__} 启动")
    logging.info(f"日志文件: {log_file}")
    logging.info(f"审计日志: {audit_file}")
    if verbose:
        logging.info("详细模式已启用，将输出DEBUG级别日志到控制台")
