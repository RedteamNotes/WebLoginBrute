#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from unittest.mock import patch

from pydantic import ValidationError as PydanticValidationError

from webloginbrute.config import Config
from webloginbrute.exceptions import ValidationError


class TestConfig(unittest.TestCase):
    """测试配置功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.users_file = os.path.join(self.temp_dir, "users.txt")
        self.passwords_file = os.path.join(self.temp_dir, "passwords.txt")

        # 创建测试文件
        with open(self.users_file, "w") as f:
            f.write("admin\nuser\n")
        with open(self.passwords_file, "w") as f:
            f.write("password\n123456\n")

    def tearDown(self):
        """清理测试环境"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_config_creation(self):
        """测试配置创建"""
        config = Config(
            url="https://example.com/login",
            action="https://example.com/auth",
            users=self.users_file,
            passwords=self.passwords_file,
            csrf="csrf_token",
            login_field="remember_me",
            login_value="1",
            cookie=None,
            timeout=30,
            threads=10,
            resume=True,
            log="progress.json",
            aggressive=2,
            dry_run=True,
            verbose=True,
            max_memory_mb=1024,
            memory_warning_threshold=80,
            memory_critical_threshold=95,
            memory_cleanup_interval=60,
            session_rotation_interval=300,
            session_lifetime=1800,
            max_session_pool_size=50,
            enable_session_rotation=True,
            rotation_strategy="time",
            enable_health_check=True,
            validate_network_connectivity=True,
            validate_file_integrity=True,
            max_file_size=100,
            security_level="standard",
            allowed_domains=["example.com"],
            blocked_domains=["malicious.com"],
        )

        self.assertEqual(config.url, "https://example.com/login")
        self.assertEqual(config.action, "https://example.com/auth")
        self.assertEqual(config.users, self.users_file)
        self.assertEqual(config.passwords, self.passwords_file)
        self.assertEqual(config.csrf, "csrf_token")
        self.assertEqual(config.login_field, "remember_me")
        self.assertEqual(config.login_value, "1")
        self.assertIsNone(config.cookie)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.threads, 10)
        self.assertTrue(config.resume)
        self.assertEqual(config.log, "progress.json")
        self.assertEqual(config.aggressive, 2)
        self.assertTrue(config.dry_run)
        self.assertTrue(config.verbose)

    def test_config_defaults(self):
        """测试配置默认值"""
        config = Config(
            url="https://example.com/login",
            action="https://example.com/authenticate",
            users=self.users_file,
            passwords=self.passwords_file,
            csrf=None,
            timeout=30,
            threads=10,
            log="test.log",
            aggressive=1,
            login_field=None,
            login_value=None,
            cookie=None,
            resume=False,
            dry_run=False,
        )

        # 测试默认值
        self.assertIsNone(config.login_field)
        self.assertIsNone(config.login_value)
        self.assertIsNone(config.cookie)
        self.assertFalse(config.resume)
        self.assertFalse(config.dry_run)
        self.assertFalse(config.verbose)

    def test_config_validation(self):
        """测试配置验证"""
        # 测试有效配置
        config = Config(
            url="https://example.com/login",
            action="https://example.com/authenticate",
            users=self.users_file,
            passwords=self.passwords_file,
            csrf=None,
            timeout=30,
            threads=10,
            log="test.log",
            aggressive=1,
            login_field=None,
            login_value=None,
            cookie=None,
            resume=False,
            dry_run=False,
        )

        # 验证应该通过
        self.assertIsNotNone(config)

        # 测试无效URL
        with self.assertRaises(ValidationError):
            Config(
                url="invalid-url",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                csrf=None,
                timeout=30,
                threads=10,
                log="test.log",
                aggressive=1,
                login_field=None,
                login_value=None,
                cookie=None,
                resume=False,
                dry_run=False,
            )

    def test_config_file_validation(self):
        """测试配置文件验证"""
        # 测试文件不存在
        with self.assertRaises(ValidationError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users="/nonexistent/users.txt",
                passwords=self.passwords_file,
                csrf=None,
                timeout=30,
                threads=10,
                log="test.log",
                aggressive=1,
                login_field=None,
                login_value=None,
                cookie=None,
                resume=False,
                dry_run=False,
            )

    def test_config_threads_validation(self):
        """测试线程数验证"""
        # 测试线程数过小
        with self.assertRaises(PydanticValidationError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                csrf=None,
                timeout=30,
                threads=0,
                log="test.log",
                aggressive=1,
                login_field=None,
                login_value=None,
                cookie=None,
                resume=False,
                dry_run=False,
            )

        # 测试线程数过大
        with self.assertRaises(PydanticValidationError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                csrf=None,
                timeout=30,
                threads=101,
                log="test.log",
                aggressive=1,
                login_field=None,
                login_value=None,
                cookie=None,
                resume=False,
                dry_run=False,
            )

    def test_config_timeout_validation(self):
        """测试超时验证"""
        # 测试超时过小
        with self.assertRaises(PydanticValidationError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                csrf=None,
                timeout=0,
                threads=10,
                log="test.log",
                aggressive=1,
                login_field=None,
                login_value=None,
                cookie=None,
                resume=False,
                dry_run=False,
            )

    def test_config_aggressive_validation(self):
        """测试对抗级别验证"""
        # 测试无效对抗级别
        with self.assertRaises(PydanticValidationError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                csrf=None,
                timeout=30,
                threads=10,
                log="test.log",
                aggressive=4,
                login_field=None,
                login_value=None,
                cookie=None,
                resume=False,
                dry_run=False,
            )

    def test_config_with_custom_fields(self):
        """测试带自定义字段的配置"""
        config = Config(
            url="https://example.com/login",
            action="https://example.com/authenticate",
            users=self.users_file,
            passwords=self.passwords_file,
            csrf=None,
            timeout=30,
            threads=10,
            log="test.log",
            aggressive=1,
            login_field="domain",
            login_value="example.com",
            cookie=None,
            resume=False,
            dry_run=False,
        )

        self.assertEqual(config.login_field, "domain")
        self.assertEqual(config.login_value, "example.com")

    def test_config_with_cookie(self):
        """测试带Cookie的配置"""
        cookie_file = os.path.join(self.temp_dir, "cookies.txt")
        with open(cookie_file, "w") as f:
            f.write("session=abc123")

        config = Config(
            url="https://example.com/login",
            action="https://example.com/authenticate",
            users=self.users_file,
            passwords=self.passwords_file,
            csrf=None,
            timeout=30,
            threads=10,
            log="test.log",
            aggressive=1,
            cookie=cookie_file,
            login_field=None,
            login_value=None,
            resume=False,
            dry_run=False,
        )

        self.assertEqual(config.cookie, cookie_file)

    def test_config_with_csrf(self):
        """测试带CSRF的配置"""
        config = Config(
            url="https://example.com/login",
            action="https://example.com/authenticate",
            users=self.users_file,
            passwords=self.passwords_file,
            csrf="csrf_token",
            timeout=30,
            threads=10,
            log="test.log",
            aggressive=1,
            login_field=None,
            login_value=None,
            cookie=None,
            resume=False,
            dry_run=False,
        )

        self.assertEqual(config.csrf, "csrf_token")

    def test_config_aggressive_levels(self):
        """测试所有对抗级别"""
        valid_levels = [0, 1, 2, 3]
        for level in valid_levels:
            config = Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                csrf=None,
                timeout=30,
                threads=10,
                log="test.log",
                aggressive=level,
                login_field=None,
                login_value=None,
                cookie=None,
                resume=False,
                dry_run=False,
            )
            self.assertEqual(config.aggressive, level)

    def test_config_boolean_flags(self):
        """测试布尔标志"""
        config = Config(
            url="https://example.com/login",
            action="https://example.com/authenticate",
            users=self.users_file,
            passwords=self.passwords_file,
            csrf=None,
            timeout=30,
            threads=10,
            log="test.log",
            aggressive=1,
            resume=True,
            dry_run=True,
            verbose=True,
            login_field=None,
            login_value=None,
            cookie=None,
        )

        self.assertTrue(config.resume)
        self.assertTrue(config.dry_run)
        self.assertTrue(config.verbose)

    def test_config_creation_with_invalid_cookie(self):
        """测试带无效Cookie的配置"""
        with self.assertRaises(ValidationError):
            Config(
                url="https://example.com/login",
                action="https://example.com/auth",
                users=self.users_file,
                passwords=self.passwords_file,
                csrf="csrf_token",
                login_field="remember_me",
                login_value="1",
                cookie="cookies.txt",  # 不存在的文件
                timeout=30,
                threads=10,
                resume=True,
                log="progress.json",
                aggressive=2,
                dry_run=True,
                verbose=True,
            )

    @patch("argparse.ArgumentParser.parse_args")
    def test_parse_args(self, mock_parse_args):
        """测试命令行参数解析"""
        # 模拟命令行参数
        mock_args = type(
            "Args",
            (),
            {
                "config": None,
                "url": "https://example.com/login",
                "action": "https://example.com/authenticate",
                "users": self.users_file,
                "passwords": self.passwords_file,
                "csrf": None,
                "login_field": None,
                "login_value": None,
                "cookie": None,
                "timeout": None,
                "threads": None,
                "resume": False,
                "log": None,
                "aggressive": 1,
                "dry_run": False,
                "verbose": False,
                "version": False,
                "enable_session_rotation": True,
            },
        )()

        # 直接返回args对象，而不是元组
        mock_parse_args.return_value = mock_args

        # 调用实际的parse_args方法
        args, defaults = Config.parse_args()

        # 验证返回的参数
        self.assertEqual(args.url, "https://example.com/login")
        self.assertEqual(args.action, "https://example.com/authenticate")
        self.assertEqual(args.users, self.users_file)
        self.assertEqual(args.passwords, self.passwords_file)


if __name__ == "__main__":
    unittest.main()
 