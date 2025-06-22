#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import requests
from unittest.mock import patch, Mock
from requests.exceptions import Timeout

from webloginbrute.http_client import HttpClient
from webloginbrute.exceptions import NetworkError


class TestHttpClient(unittest.TestCase):
    """测试HTTP客户端功能"""

    def setUp(self):
        """设置测试环境"""
        # 创建模拟配置对象
        self.mock_config = Mock()
        self.mock_config.timeout = 30
        self.mock_config.max_retries = 3
        self.mock_config.base_delay = 1.0
        self.mock_config.session_rotation_interval = 300
        self.mock_config.session_lifetime = 600
        self.mock_config.max_session_pool_size = 100
        self.mock_config.enable_session_rotation = True
        self.mock_config.rotation_strategy = "time"
        self.mock_config.cookie = None

        self.client = HttpClient(self.mock_config)

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.client.config, self.mock_config)
        self.assertEqual(self.client.max_retries, 3)
        self.assertEqual(self.client.base_delay, 1.0)
        self.assertIsNotNone(self.client.session_rotator)
        self.assertIsNotNone(self.client.memory_manager)
        self.assertIsNotNone(self.client._dns_cache)

    @patch("webloginbrute.http_client.requests.Session")
    def test_get_request(self, mock_session):
        """测试GET请求"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "text/html"}

        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance

        with patch.object(
            self.client.session_rotator,
            "get_session",
            return_value=mock_session_instance,
        ):
            with patch.object(
                self.client, "_validate_response_headers", return_value=True
            ):
                with patch.object(self.client.session_rotator, "record_request"):
                    response = self.client.get("https://example.com")

                    self.assertEqual(response, mock_response)
                    mock_session_instance.request.assert_called_once()

    @patch("webloginbrute.http_client.requests.Session")
    def test_post_request(self, mock_session):
        """测试POST请求"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {"Content-Type": "text/html"}

        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance

        with patch.object(
            self.client.session_rotator,
            "get_session",
            return_value=mock_session_instance,
        ):
            with patch.object(
                self.client, "_validate_response_headers", return_value=True
            ):
                with patch.object(self.client.session_rotator, "record_request"):
                    response = self.client.post(
                        "https://example.com", data={"key": "value"}
                    )

                    self.assertEqual(response, mock_response)
                    mock_session_instance.request.assert_called_once()

    @patch("webloginbrute.http_client.requests.Session")
    def test_request_timeout(self, mock_session):
        """测试请求超时"""
        mock_session_instance = Mock()
        mock_session_instance.request.side_effect = Timeout("Request timeout")
        mock_session.return_value = mock_session_instance

        with patch.object(
            self.client.session_rotator,
            "get_session",
            return_value=mock_session_instance,
        ):
            with patch.object(self.client.session_rotator, "record_request"):
                with self.assertRaises(NetworkError):
                    self.client.get("https://example.com")

    @patch("webloginbrute.http_client.requests.Session")
    def test_request_connection_error(self, mock_session):
        """测试连接错误"""
        mock_session_instance = Mock()
        mock_session_instance.request.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )
        mock_session.return_value = mock_session_instance

        with patch.object(
            self.client.session_rotator,
            "get_session",
            return_value=mock_session_instance,
        ):
            with patch.object(self.client.session_rotator, "record_request"):
                with self.assertRaises(NetworkError):
                    self.client.get("https://example.com")

    @patch("webloginbrute.http_client.requests.Session")
    def test_http_error(self, mock_session):
        """测试HTTP错误"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Not Found", response=mock_response
        )

        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance

        with patch.object(
            self.client.session_rotator,
            "get_session",
            return_value=mock_session_instance,
        ):
            with patch.object(self.client.session_rotator, "record_request"):
                with self.assertRaises(NetworkError):
                    self.client.get("https://example.com")

    def test_validate_response_headers(self):
        """测试响应头验证"""
        # 测试正常响应头
        normal_response = Mock()
        normal_response.headers = {"Content-Type": "text/html", "Server": "nginx"}
        self.assertTrue(self.client._validate_response_headers(normal_response))

        # 测试过大响应头
        large_response = Mock()
        large_response.headers = {"X-Large-Header": "x" * 10000}  # 10KB header
        self.assertFalse(self.client._validate_response_headers(large_response))

    def test_close_all_sessions(self):
        """测试关闭所有会话"""
        with patch.object(self.client.session_rotator, "cleanup") as mock_cleanup:
            self.client.close_all_sessions()
            mock_cleanup.assert_called_once()

    def test_get_session_stats(self):
        """测试获取会话统计"""
        mock_stats = {
            "total_sessions": 5,
            "total_requests": 100,
            "total_errors": 2,
            "avg_error_rate": 0.02,
            "rotation_stats": {"total_rotations": 3},
        }

        with patch.object(
            self.client.session_rotator, "get_pool_stats", return_value=mock_stats
        ):
            stats = self.client.get_session_stats()
            self.assertEqual(stats, mock_stats)

    def test_get_memory_stats(self):
        """测试获取内存统计"""
        mock_stats = {"peak_memory": 150.5, "cleanup_count": 5, "gc_count": 10}

        with patch.object(
            self.client.memory_manager, "get_memory_stats", return_value=mock_stats
        ):
            stats = self.client.get_memory_stats()
            self.assertEqual(stats, mock_stats)

    def test_resolve_host(self):
        """测试主机解析"""
        with patch("socket.gethostbyname", return_value="192.168.1.1"):
            ip = self.client._resolve_host("example.com")
            self.assertEqual(ip, "192.168.1.1")

            # 测试缓存
            ip2 = self.client._resolve_host("example.com")
            self.assertEqual(ip2, "192.168.1.1")

    def test_resolve_host_failure(self):
        """测试主机解析失败"""
        with patch("socket.gethostbyname", side_effect=Exception("DNS error")):
            ip = self.client._resolve_host("invalid.com")
            self.assertIsNone(ip)


if __name__ == "__main__":
    unittest.main()
