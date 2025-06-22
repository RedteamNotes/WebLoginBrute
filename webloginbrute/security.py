#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import ipaddress
import logging
import os
import re
from urllib.parse import urlparse

from .constants import SECURITY_CONFIG
from .exceptions import SecurityError

# 危险字符集合，使用 set 提升检测性能
DANGEROUS_CHARS = {
    '\0', '\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07',
    '\x08', '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f'
}

def check_dangerous_chars(filepath: str) -> bool:
    """检查路径中是否包含危险字符"""
    return any(char in filepath for char in DANGEROUS_CHARS)

class SecurityManager:
    """安全管理器"""

    @staticmethod
    def hash_sensitive_data(data):
        """对敏感数据进行hash处理"""
        if not data:
            return "***"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def sanitize_input(input_str):
        """清理和验证用户输入"""
        if not input_str:
            return ""

        # 移除危险字符
        dangerous_chars = [
            "<",
            ">",
            '"',
            "'",
            "&",
            ";",
            "|",
            "`",
            "$",
            "(",
            ")",
            "{",
            "}",
        ]
        for char in dangerous_chars:
            input_str = input_str.replace(char, "")

        # 限制长度
        if len(input_str) > 1000:
            input_str = input_str[:1000]

        return input_str.strip()

    @staticmethod
    def validate_url(url, allow_private_networks=False):
        """验证URL安全性"""
        if not url:
            return False

        try:
            parsed = urlparse(url)
            # 检查协议
            if parsed.scheme not in ["http", "https"]:
                return False

            # 检查域名 - 使用hostname而不是netloc
            if not parsed.hostname:
                return False

            # 检查是否为本地地址
            if parsed.hostname in ["localhost", "127.0.0.1", "::1"]:
                return allow_private_networks

            # 检查是否为私有IP
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private:
                    return allow_private_networks
            except ValueError:
                pass

            return True
        except ValueError:
            return False

    @staticmethod
    def check_rate_limit(request_count, time_window=60):
        """检查请求频率限制"""
        # 简单的频率限制实现
        if request_count > SECURITY_CONFIG["max_request_rate"]:
            return False
        return True

    @staticmethod
    def check_ip_whitelist(ip_address):
        """检查IP是否在白名单中"""
        if not SECURITY_CONFIG["ip_whitelist"]:
            return True  # 白名单为空时允许所有IP
        return ip_address in SECURITY_CONFIG["ip_whitelist"]

    @staticmethod
    def check_ip_blacklist(ip_address):
        """检查IP是否在黑名单中"""
        return ip_address not in SECURITY_CONFIG["ip_blacklist"]

    @staticmethod
    def get_safe_path(filepath):
        """获取安全的文件路径，防止路径遍历攻击 - 改进版本"""
        if not filepath:
            raise SecurityError("文件路径不能为空")

        # 规范化路径
        normalized_path = os.path.normpath(filepath)

        # 检查路径长度
        if len(normalized_path) > SECURITY_CONFIG["max_path_length"]:
            raise SecurityError(
                f"文件路径过长: {len(normalized_path)} > {SECURITY_CONFIG['max_path_length']}"
            )

        # 检查符号链接
        try:
            if os.path.islink(normalized_path):
                logging.warning(f"检测到符号链接，拒绝访问: {filepath}")
                raise SecurityError(f"不允许访问符号链接: {filepath}")
        except OSError:
            # 文件不存在，继续检查
            pass

        # 检查绝对路径
        if os.path.isabs(normalized_path):
            # 检查是否访问系统敏感目录
            for forbidden_path in SECURITY_CONFIG["forbidden_paths"]:
                if normalized_path.startswith(forbidden_path):
                    raise SecurityError(f"不允许访问系统目录: {forbidden_path}")

            # 确保路径在当前目录下
            current_dir = os.path.realpath(os.getcwd())
            real_path = os.path.realpath(normalized_path)
            if not real_path.startswith(current_dir):
                raise SecurityError(f"不允许访问当前目录外的文件: {filepath}")

        # 改进的路径遍历检测 - 更严格的检查
        path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"\.\.\\\\",
            r"\.\.\.",
            r"\.\.\.\.",
            r"\.\.",  # 检测单独的..
            r"\.\.\.",  # 检测三个点
            r"\.\.\.\.",  # 检测四个点
            r"\.\.\.\.\.",  # 检测五个点
            r"\.\.\.\.\.\.",  # 检测六个点
            r"\.\.\.\.\.\.\.",  # 检测七个点
            r"\.\.\.\.\.\.\.\.",  # 检测八个点
            r"\.\.\.\.\.\.\.\.\.",  # 检测九个点
            r"\.\.\.\.\.\.\.\.\.\.",  # 检测十个点
        ]

        for pattern in path_traversal_patterns:
            if re.search(pattern, filepath, re.IGNORECASE):
                raise SecurityError(f"路径包含遍历模式: {pattern}")

        # 检查路径中的危险字符
        if check_dangerous_chars(filepath):
            raise SecurityError(f"路径包含危险字符")

        # 检查路径是否为空或只包含空白字符
        if not normalized_path.strip():
            raise SecurityError("路径不能为空或只包含空白字符")

        # 检查文件扩展名
        _, ext = os.path.splitext(normalized_path)
        if ext and ext.lower() not in SECURITY_CONFIG["allowed_file_extensions"]:
            raise SecurityError(f"不允许的文件扩展名: {ext}")

        # 额外的安全检查：确保路径不包含可疑的绝对路径模式
        suspicious_absolute_patterns = [
            r"^/[a-zA-Z]*/[a-zA-Z]*/[a-zA-Z]*$",  # Unix绝对路径命令
            r"^[A-Z]:\\[a-zA-Z]*\\[a-zA-Z]*\\[a-zA-Z]*$",  # Windows绝对路径命令
            r"^[A-Z]:/[a-zA-Z]*/[a-zA-Z]*/[a-zA-Z]*$",  # Windows混合路径
        ]

        for pattern in suspicious_absolute_patterns:
            if re.search(pattern, filepath, re.IGNORECASE):
                raise SecurityError(f"路径包含可疑的绝对路径模式: {pattern}")

        return normalized_path
