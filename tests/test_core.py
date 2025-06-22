#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from unittest.mock import patch, Mock

from webloginbrute.config import Config
from webloginbrute.core import WebLoginBrute


class TestWebLoginBrute(unittest.TestCase):
    """测试WebLoginBrute核心功能"""

    def setUp(self):
        """设置测试环境"""
        # 创建临时文件用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.users_file = os.path.join(self.temp_dir, "users.txt")
        self.passwords_file = os.path.join(self.temp_dir, "passwords.txt")

        # 创建测试文件
        with open(self.users_file, "w") as f:
            f.write("admin\nuser\n")
        with open(self.passwords_file, "w") as f:
            f.write("password\n123456\n")

        # 创建测试配置
        self.config = Config(
            url="https://example.com/login",
            action="https://example.com/auth",
            users=self.users_file,
            passwords=self.passwords_file,
            csrf="csrf_token",
            login_field="remember_me",
            login_value="1",
            cookie=None,
            timeout=30,
            threads=5,
            resume=False,
            log="test.log",
            aggressive=1,
            dry_run=False,
            verbose=False,
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

    def tearDown(self):
        """清理测试环境"""
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch("webloginbrute.core.setup_logging")
    @patch("webloginbrute.core.HttpClient")
    @patch("webloginbrute.core.StateManager")
    @patch("webloginbrute.core.StatsManager")
    def test_initialization(self, mock_stats, mock_state, mock_http, mock_logging):
        """测试初始化"""
        brute = WebLoginBrute(self.config)

        self.assertEqual(brute.config, self.config)
        self.assertFalse(brute.success.is_set())
        self.assertIsNone(brute.executor)
        self.assertFalse(brute._shutdown_requested)

    @patch("webloginbrute.core.setup_logging")
    @patch("webloginbrute.core.HttpClient")
    @patch("webloginbrute.core.StateManager")
    @patch("webloginbrute.core.StatsManager")
    def test_signal_handler(self, mock_stats, mock_state, mock_http, mock_logging):
        """测试信号处理"""
        brute = WebLoginBrute(self.config)

        # 模拟信号处理
        brute._signal_handler(2, None)  # SIGINT

        self.assertTrue(brute._shutdown_requested)
        self.assertTrue(brute.success.is_set())

    @patch("webloginbrute.core.setup_logging")
    @patch("webloginbrute.core.HttpClient")
    @patch("webloginbrute.core.StateManager")
    @patch("webloginbrute.core.StatsManager")
    @patch("webloginbrute.core.load_wordlist")
    def test_load_wordlists(
        self, mock_load_wordlist, mock_stats, mock_state, mock_http, mock_logging
    ):
        """测试字典加载"""
        mock_load_wordlist.return_value = ["admin", "user"]

        # 模拟状态管理器的load_progress方法
        mock_state_instance = Mock()
        mock_state_instance.load_progress.return_value = (set(), {})
        mock_state.return_value = mock_state_instance

        brute = WebLoginBrute(self.config)
        brute._load_wordlists()

        self.assertEqual(brute.usernames, ["admin", "user"])
        self.assertEqual(brute.passwords, ["admin", "user"])

    @patch("webloginbrute.core.setup_logging")
    @patch("webloginbrute.core.HttpClient")
    @patch("webloginbrute.core.StateManager")
    @patch("webloginbrute.core.StatsManager")
    @patch("webloginbrute.core.ThreadPoolExecutor")
    def test_setup_executor(
        self, mock_executor, mock_stats, mock_state, mock_http, mock_logging
    ):
        """测试线程池设置"""
        mock_executor_instance = Mock()
        mock_executor.return_value = mock_executor_instance

        brute = WebLoginBrute(self.config)
        brute._setup_executor()

        self.assertEqual(brute.executor, mock_executor_instance)
        self.assertIsNotNone(brute.stats.stats["start_time"])

    @patch("webloginbrute.core.setup_logging")
    @patch("webloginbrute.core.HttpClient")
    @patch("webloginbrute.core.StateManager")
    @patch("webloginbrute.core.StatsManager")
    def test_build_login_data(self, mock_stats, mock_state, mock_http, mock_logging):
        """测试登录数据构建"""
        brute = WebLoginBrute(self.config)

        # 测试基本数据构建（包含配置中的login_field）
        data = brute._build_login_data("admin", "password", None)
        self.assertEqual(
            data,
            {
                "username": "admin",
                "password": "password",
                "remember_me": "1",  # 配置中设置的login_field和login_value
            },
        )

        # 测试带CSRF token的数据构建
        self.config.csrf = "csrf_token"
        data = brute._build_login_data("admin", "password", "abc123")
        self.assertEqual(
            data,
            {
                "username": "admin",
                "password": "password",
                "csrf_token": "abc123",
                "remember_me": "1",  # 配置中设置的login_field和login_value
            },
        )

        # 测试带额外字段的数据构建
        self.config.login_field = "domain"
        self.config.login_value = "example.com"
        data = brute._build_login_data("admin", "password", "abc123")
        self.assertEqual(
            data,
            {
                "username": "admin",
                "password": "password",
                "csrf_token": "abc123",
                "domain": "example.com",  # 新的login_field和login_value
            },
        )

    @patch("webloginbrute.core.setup_logging")
    @patch("webloginbrute.core.HttpClient")
    @patch("webloginbrute.core.StateManager")
    @patch("webloginbrute.core.StatsManager")
    def test_check_login_success(self, mock_stats, mock_state, mock_http, mock_logging):
        """测试登录成功判断"""
        brute = WebLoginBrute(self.config)

        # 模拟成功响应
        success_response = Mock()
        success_response.text = "Welcome to dashboard"
        self.assertTrue(brute._check_login_success(success_response))

        # 模拟失败响应
        failure_response = Mock()
        failure_response.text = "Invalid credentials"
        self.assertFalse(brute._check_login_success(failure_response))

        # 测试自定义关键词
        custom_response = Mock()
        custom_response.text = "Login successful"
        self.assertTrue(
            brute._check_login_success(
                custom_response,
                success_keywords=["successful"],
                failure_keywords=["invalid"],
            )
        )

    @patch("webloginbrute.core.setup_logging")
    @patch("webloginbrute.core.HttpClient")
    @patch("webloginbrute.core.StateManager")
    @patch("webloginbrute.core.StatsManager")
    def test_cleanup_resources(self, mock_stats, mock_state, mock_http, mock_logging):
        """测试资源清理"""
        mock_executor = Mock()
        mock_http_instance = Mock()
        mock_state_instance = Mock()
        mock_stats_instance = Mock()

        # 设置mock对象的方法
        mock_http_instance.close_all_sessions = Mock()
        mock_state_instance.cleanup_progress_file = Mock()
        mock_stats_instance.finalize = Mock()
        mock_stats_instance.print_final_report = Mock()
        mock_stats_instance.stats = {}

        mock_http.return_value = mock_http_instance
        mock_state.return_value = mock_state_instance
        mock_stats.return_value = mock_stats_instance

        brute = WebLoginBrute(self.config)
        brute.executor = mock_executor
        brute.success.set()

        brute._cleanup_resources()

        # 验证线程池关闭
        mock_executor.shutdown.assert_called_once_with(wait=False, cancel_futures=True)

        # 验证其他资源清理
        mock_stats_instance.finalize.assert_called_once()
        mock_stats_instance.print_final_report.assert_called_once()
        mock_state_instance.cleanup_progress_file.assert_called_once()
        mock_http_instance.close_all_sessions.assert_called_once()


if __name__ == "__main__":
    unittest.main()
