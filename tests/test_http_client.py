#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch, Mock, MagicMock
import requests
from requests.exceptions import RequestException, Timeout

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
        self.mock_config.session_lifetime = 300
        self.mock_config.max_session_pool_size = 100
        self.mock_config.cookie = None
        
        self.client = HttpClient(self.mock_config)

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.client.config, self.mock_config)
        self.assertEqual(self.client.max_retries, 3)
        self.assertEqual(self.client.base_delay, 1.0)
        self.assertEqual(self.client.session_lifetime, 300)
        self.assertEqual(self.client.max_session_pool_size, 100)
        self.assertIsNotNone(self.client._session_pool)
        self.assertIsNotNone(self.client._dns_cache)

    @patch('webloginbrute.http_client.requests.Session')
    def test_get_request(self, mock_session):
        """测试GET请求"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        with patch.object(self.client, '_get_session', return_value=mock_session_instance):
            with patch.object(self.client, '_validate_response_headers', return_value=True):
                response = self.client.get("https://example.com")
                
                self.assertEqual(response, mock_response)
                mock_session_instance.request.assert_called_once()

    @patch('webloginbrute.http_client.requests.Session')
    def test_post_request(self, mock_session):
        """测试POST请求"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        with patch.object(self.client, '_get_session', return_value=mock_session_instance):
            with patch.object(self.client, '_validate_response_headers', return_value=True):
                response = self.client.post("https://example.com", data={"key": "value"})
                
                self.assertEqual(response, mock_response)
                mock_session_instance.request.assert_called_once()

    @patch('webloginbrute.http_client.requests.Session')
    def test_request_timeout(self, mock_session):
        """测试请求超时"""
        mock_session_instance = Mock()
        mock_session_instance.request.side_effect = Timeout("Request timeout")
        mock_session.return_value = mock_session_instance
        
        with patch.object(self.client, '_get_session', return_value=mock_session_instance):
            with self.assertRaises(NetworkError):
                self.client.get("https://example.com")

    @patch('webloginbrute.http_client.requests.Session')
    def test_request_connection_error(self, mock_session):
        """测试连接错误"""
        mock_session_instance = Mock()
        mock_session_instance.request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        mock_session.return_value = mock_session_instance
        
        with patch.object(self.client, '_get_session', return_value=mock_session_instance):
            with self.assertRaises(NetworkError):
                self.client.get("https://example.com")

    @patch('webloginbrute.http_client.requests.Session')
    def test_http_error(self, mock_session):
        """测试HTTP错误"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not Found", response=mock_response)
        
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        with patch.object(self.client, '_get_session', return_value=mock_session_instance):
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

    def test_get_session(self):
        """测试会话获取"""
        # 测试创建新会话
        session = self.client._get_session("https://example.com:443")
        self.assertIsNotNone(session)
        
        # 测试复用会话
        session2 = self.client._get_session("https://example.com:443")
        self.assertEqual(session, session2)

    def test_close_all_sessions(self):
        """测试关闭所有会话"""
        # 创建一些会话
        self.client._get_session("https://example.com:443")
        self.client._get_session("https://test.com:443")
        
        # 验证会话池不为空
        self.assertGreater(len(self.client._session_pool), 0)
        
        # 关闭所有会话
        self.client.close_all_sessions()
        
        # 验证会话池已清空
        self.assertEqual(len(self.client._session_pool), 0)

    def test_pre_resolve_targets(self):
        """测试预解析目标"""
        urls = ["https://example.com/login", "https://test.com/api"]
        
        with patch.object(self.client, '_resolve_host') as mock_resolve:
            self.client.pre_resolve_targets(urls)
            
            # 验证DNS解析被调用
            self.assertEqual(mock_resolve.call_count, 2)
            mock_resolve.assert_any_call("example.com")
            mock_resolve.assert_any_call("test.com")

    def test_resolve_host(self):
        """测试主机解析"""
        with patch('socket.gethostbyname', return_value="192.168.1.1"):
            ip = self.client._resolve_host("example.com")
            self.assertEqual(ip, "192.168.1.1")
            
            # 测试缓存
            ip2 = self.client._resolve_host("example.com")
            self.assertEqual(ip2, "192.168.1.1")

    def test_resolve_host_failure(self):
        """测试主机解析失败"""
        with patch('socket.gethostbyname', side_effect=Exception("DNS error")):
            ip = self.client._resolve_host("invalid.com")
            self.assertIsNone(ip)


if __name__ == '__main__':
    unittest.main() 