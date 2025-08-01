#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import ipaddress
import logging
import os
import re
from urllib.parse import urlparse
import json
import time
from typing import Dict, Any, Literal
import requests

from ..constants import SECURITY_CONFIG
from ..utils.exceptions import SecurityError

# 设置日志
logging.basicConfig(level=logging.INFO)

# 危险字符集合，使用 set 提升检测性能
DANGEROUS_CHARS = {
    "\0",
    "\x00",
    "\x01",
    "\x02",
    "\x03",
    "\x04",
    "\x05",
    "\x06",
    "\x07",
    "\x08",
    "\x09",
    "\x0a",
    "\x0b",
    "\x0c",
    "\x0d",
    "\x0e",
    "\x0f",
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
            raise SecurityError("路径包含危险字符")

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

    def log_security_event(self, event_type, details, severity):
        pass

    def check_security_issues(self):
        pass

    def check_security_scan_completed(
        self, issues_found, high_severity, medium_severity, low_severity
    ):
        pass

    def _generate_report(self, report: Dict[str, Any]) -> str:
        """
        生成安全报告
        """
        if not all(k in report for k in ["passed", "failed", "details"]):
            logging.warning("安全报告格式无效")
            return ""

        summary = f"### 安全审计摘要 (等级: {self.security_level})\n"
        summary += f"- **通过:** {report['passed']} 项\n"
        summary += f"- **失败:** {report['failed']} 项\n"

        if report["failed"] > 0:
            summary += "\n**失败项详情:**\n"
            for detail in report["details"]:
                if detail["status"] == "failed":
                    summary += f"- **{detail['check_name']}:** {detail['message']}\n"

        logging.info("生成安全报告")
        return summary

    def _save_report(self, report: Dict[str, Any], format: str = "json"):
        """
        保存安全报告到文件
        """
        filename = f"security_report_{int(time.time())}.{format}"

        if format == "json":
            with open(filename, "w") as f:
                json.dump(report, f, indent=4)
            logging.info(f"安全报告已保存到 {filename}")
        else:
            logging.warning(f"不支持的报告格式: {format}")

    def _is_rate_limited(self, response: requests.Response) -> bool:
        """
        检查是否被速率限制
        """
        # 简单的速率限制检查
        if response.status_code == 429:
            logging.warning("检测到速率限制 (HTTP 429)")
            return True

        # 可以在这里添加更复杂的检查，例如检查响应内容

        return False

    def _is_suspicious_redirect(self, response: requests.Response) -> bool:
        """检查可疑重定向"""
        if response.status_code in [301, 302, 307, 308]:
            location = response.headers.get("Location", "")
            if "login" not in location and "error" not in location:
                logging.warning(f"检测到可疑重定向: {location}")
                return True
        return False

    def get_security_level(self):
        """返回当前安全级别"""
        return self.security_level

    def set_security_level(self, level: Literal["low", "standard", "high", "paranoid"]):
        """设置安全级别"""
        self.security_level = level
        logging.info(f"安全级别已设置为: {level}")
