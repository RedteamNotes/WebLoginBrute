#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from unittest.mock import patch, mock_open

from webloginbrute.config import Config


class TestConfig(unittest.TestCase):
    """测试配置类的各种功能"""

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

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_valid_config(self):
        """测试有效配置"""
        config = Config(
            url="https://example.com/login",
            action="https://example.com/authenticate",
            users=self.users_file,
            passwords=self.passwords_file
        )
        self.assertEqual(config.url, "https://example.com/login")
        self.assertEqual(config.action, "https://example.com/authenticate")
        self.assertEqual(config.users, self.users_file)
        self.assertEqual(config.passwords, self.passwords_file)

    def test_invalid_url(self):
        """测试无效URL"""
        with self.assertRaises(ValueError):
            Config(
                url="invalid-url",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file
            )

    def test_missing_file(self):
        """测试缺失文件"""
        with self.assertRaises(ValueError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users="nonexistent.txt",
                passwords=self.passwords_file
            )

    def test_optional_cookie_file(self):
        """测试可选的cookie文件"""
        cookie_file = os.path.join(self.temp_dir, "cookies.txt")
        with open(cookie_file, "w") as f:
            f.write("session=abc123")
        
        config = Config(
            url="https://example.com/login",
            action="https://example.com/authenticate",
            users=self.users_file,
            passwords=self.passwords_file,
            cookie=cookie_file
        )
        self.assertEqual(config.cookie, cookie_file)

    def test_invalid_cookie_file(self):
        """测试无效的cookie文件"""
        with self.assertRaises(ValueError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                cookie="nonexistent_cookies.txt"
            )

    def test_threads_validation(self):
        """测试线程数验证"""
        # 测试最小值
        with self.assertRaises(ValueError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                threads=0
            )
        
        # 测试最大值
        with self.assertRaises(ValueError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                threads=101
            )

    def test_timeout_validation(self):
        """测试超时验证"""
        # 测试最小值
        with self.assertRaises(ValueError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                timeout=0
            )
        
        # 测试最大值
        with self.assertRaises(ValueError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                timeout=601
            )

    def test_aggressive_validation(self):
        """测试对抗级别验证"""
        # 测试有效值
        valid_levels = ['A0', 'A1', 'A2', 'A3']
        for level in valid_levels:
            config = Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                aggressive=level
            )
            self.assertEqual(config.aggressive, level)
        
        # 测试无效值
        with self.assertRaises(ValueError):
            Config(
                url="https://example.com/login",
                action="https://example.com/authenticate",
                users=self.users_file,
                passwords=self.passwords_file,
                aggressive="A4"
            )

    @patch('argparse.ArgumentParser.parse_args')
    def test_parse_args(self, mock_parse_args):
        """测试命令行参数解析"""
        # 模拟命令行参数
        mock_args = type('Args', (), {
            'config': None,
            'url': 'https://example.com/login',
            'action': 'https://example.com/authenticate',
            'users': self.users_file,
            'passwords': self.passwords_file,
            'csrf': None,
            'login_field': None,
            'login_value': None,
            'cookie': None,
            'timeout': None,
            'threads': None,
            'resume': False,
            'log': None,
            'aggressive': None,
            'dry_run': False,
            'verbose': False,
            'version': False
        })()
        
        mock_defaults = {
            'config': None,
            'url': None,
            'action': None,
            'users': None,
            'passwords': None,
            'csrf': None,
            'login_field': None,
            'login_value': None,
            'cookie': None,
            'timeout': 30,
            'threads': 5,
            'resume': False,
            'log': 'bruteforce_progress.json',
            'aggressive': 'A1',
            'dry_run': False,
            'verbose': False,
            'version': False
        }
        
        mock_parse_args.return_value = (mock_args, mock_defaults)
        
        # 测试参数解析
        args, defaults = Config.parse_args()
        self.assertEqual(args.url, 'https://example.com/login')
        self.assertEqual(args.action, 'https://example.com/authenticate')


if __name__ == '__main__':
    unittest.main()
