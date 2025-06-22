#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import signal
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event, RLock
from typing import List

from .config import Config
from .exceptions import RateLimitError, MemoryError
from .http_client import HttpClient
from .logger import setup_logging
from .parsers import analyze_form_fields, contains_captcha, extract_token
from .reporting import StatsManager
from .state import StateManager
from .wordlists import load_wordlist
from .memory_manager import get_memory_manager, MemoryConfig
from .session_manager import get_session_rotator, SessionConfig


class WebLoginBrute:
    """
    核心流程调度类，负责整体爆破流程的编排与异常处理。
    """

    def __init__(self, config: Config) -> None:
        assert config.url and config.action and config.users and config.passwords, "核心配置参数不能为空"
        self.config = config
        setup_logging(config.verbose)
        
        # 初始化内存管理器
        memory_config = MemoryConfig(
            max_memory_mb=getattr(config, 'max_memory_mb', 500),
            warning_threshold=getattr(config, 'memory_warning_threshold', 0.8),
            critical_threshold=getattr(config, 'memory_critical_threshold', 0.9),
            cleanup_interval=getattr(config, 'memory_cleanup_interval', 60)
        )
        self.memory_manager = get_memory_manager()
        self.memory_manager.config = memory_config
        
        # 初始化会话轮换器
        session_config = SessionConfig(
            rotation_interval=getattr(config, 'session_rotation_interval', 300),
            session_lifetime=getattr(config, 'session_lifetime', 600),
            max_session_pool_size=getattr(config, 'max_session_pool_size', 100),
            enable_rotation=getattr(config, 'enable_session_rotation', True),
            rotation_strategy=getattr(config, 'rotation_strategy', 'time')
        )
        self.session_rotator = get_session_rotator()
        self.session_rotator.config = session_config
        
        # 初始化其他组件
        self.http = HttpClient(config)
        self.state = StateManager(config)
        self.stats = StatsManager()
        self.success = Event()
        self.executor = None
        self._shutdown_requested = False
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 启动内存监控
        self.memory_manager.start_monitoring()
        
        # 添加内存清理回调
        self.memory_manager.add_cleanup_callback(self._on_memory_cleanup)

    def _signal_handler(self, signum, frame):
        """处理中断信号"""
        logging.info(f"收到信号 {signum}，正在优雅关闭...")
        self._shutdown_requested = True
        self.success.set()
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None

    def _on_memory_cleanup(self, cleanup_type: str):
        """内存清理回调"""
        if cleanup_type == 'emergency':
            logging.warning("执行紧急内存清理，暂停任务执行")
            # 暂停任务执行
            if self.executor:
                self.executor.shutdown(wait=False)
                self.executor = None
        else:
            logging.debug("执行正常内存清理")

    def run(self) -> None:
        """主运行方法"""
        assert self.config.url and self.config.action and self.config.users and self.config.passwords, "核心配置参数不能为空"
        logging.info("开始WebLoginBrute主流程...")
        
        try:
            self._initialize_components()
            self._load_wordlists()
            self._setup_executor()
            self._execute_brute_force()
        except KeyboardInterrupt:
            self._handle_interruption()
        except MemoryError as e:
            logging.error(f"内存不足: {e}")
            self._handle_memory_error(e)
        except Exception as e:
            self._handle_error(e)
        finally:
            self._cleanup_resources()

    def _initialize_components(self):
        """初始化组件"""
        self.http.pre_resolve_targets([self.config.url, self.config.action])
        logging.info("组件初始化完成")

    def _load_wordlists(self):
        """加载字典文件"""
        try:
            # 估算字典文件大小
            from .wordlists import estimate_wordlist_size
            
            users_info = estimate_wordlist_size(self.config.users)
            passwords_info = estimate_wordlist_size(self.config.passwords)
            
            logging.info(f"用户名字典: {users_info['file_size_mb']:.1f}MB, 预估行数: {users_info['estimated_lines']}")
            logging.info(f"密码字典: {passwords_info['file_size_mb']:.1f}MB, 预估行数: {passwords_info['estimated_lines']}")
            
            # 检查内存需求
            total_memory_needed = (users_info.get('estimated_memory_mb', 0) + 
                                 passwords_info.get('estimated_memory_mb', 0))
            
            if not self.memory_manager.check_memory_limit(total_memory_needed):
                raise MemoryError(f"预估内存需求 {total_memory_needed:.1f}MB 超过限制")
            
            # 加载字典
            usernames = list(load_wordlist(self.config.users, self.config))
            passwords = list(load_wordlist(self.config.passwords, self.config))
            
            logging.info(f"加载了 {len(usernames)} 个用户名和 {len(passwords)} 个密码")
            
            # 恢复进度
            loaded_attempts, stats_from_file = self.state.load_progress()
            if stats_from_file:
                self.stats.update_from_progress(stats_from_file)
            
            self.usernames = usernames
            self.passwords = passwords
            
        except MemoryError as e:
            logging.error(f"内存不足，无法加载字典: {e}")
            raise
        except Exception as e:
            logging.error(f"加载字典失败: {e}")
            raise

    def _setup_executor(self):
        """设置线程池"""
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.threads, thread_name_prefix="WebLoginBrute"
        )
        self.stats.stats["start_time"] = time.time()
        logging.info("线程池设置完成")

    def _execute_brute_force(self):
        """执行暴力破解"""
        self._brute_force(self.usernames, self.passwords)

    def _handle_interruption(self):
        """处理用户中断"""
        logging.info("用户中断操作，保存进度...")
        self.state.save_progress(self.stats.get_stats())

    def _handle_memory_error(self, error: MemoryError):
        """处理内存错误"""
        logging.error(f"内存不足: {error}")
        logging.info("尝试释放内存并保存进度...")
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        # 保存进度
        self.state.save_progress(self.stats.get_stats())
        
        # 建议用户减少并发数或字典大小
        logging.info("建议: 减少并发线程数或使用更小的字典文件")

    def _handle_error(self, error):
        """处理运行错误"""
        logging.error(f"运行过程中发生错误: {error}")
        self.state.save_progress(self.stats.get_stats())

    def _cleanup_resources(self):
        """清理资源"""
        # 确保线程池正确关闭
        if self.executor:
            try:
                # 先取消所有未完成的任务
                self.executor.shutdown(wait=False, cancel_futures=True)
                logging.debug("线程池已关闭，所有未完成任务已取消")
            except Exception as e:
                logging.warning(f"关闭线程池时发生错误: {e}")
            finally:
                self.executor = None
        
        # 停止内存监控
        self.memory_manager.stop_monitoring()
        
        # 确保所有资源都被释放
        try:
            self.stats.stats["end_time"] = time.time()
            self.stats.finalize()
            self.stats.print_final_report()
            
            # 打印内存和会话统计
            self._print_resource_stats()
            
            if self.success.is_set():
                self.state.cleanup_progress_file()
            self.http.close_all_sessions()
        except Exception as e:
            logging.error(f"清理资源时发生错误: {e}")
        finally:
            import logging as _logging
            _logging.shutdown()

    def _print_resource_stats(self):
        """打印资源统计信息"""
        try:
            # 内存统计
            memory_stats = self.memory_manager.get_memory_stats()
            logging.info("内存使用统计:")
            logging.info(f"  峰值内存: {memory_stats['peak_memory']:.1f}MB")
            logging.info(f"  清理次数: {memory_stats['cleanup_count']}")
            logging.info(f"  垃圾回收: {memory_stats['gc_count']}")
            
            # 会话统计
            session_stats = self.http.get_session_stats()
            logging.info("会话管理统计:")
            logging.info(f"  总会话数: {session_stats['total_sessions']}")
            logging.info(f"  总请求数: {session_stats['total_requests']}")
            logging.info(f"  平均错误率: {session_stats['avg_error_rate']:.2%}")
            logging.info(f"  会话轮换: {session_stats['rotation_stats']['total_rotations']}")
            
        except Exception as e:
            logging.warning(f"获取资源统计失败: {e}")

    def _brute_force(self, usernames: List[str], passwords: List[str]):
        total_combinations = len(usernames) * len(passwords)
        logging.info(f"开始暴力破解，总共 {total_combinations} 个组合")
        # 过滤已尝试的组合
        combinations = [
            (u, p)
            for u in usernames
            for p in passwords
            if not self.state.has_been_attempted((u, p))
        ]
        logging.info(f"过滤后剩余 {len(combinations)} 个组合")
        # 提交任务到线程池
        if not self.executor:
            raise RuntimeError("线程池未初始化")
        futures = []
        for username, password in combinations:
            if self.success.is_set() or self._shutdown_requested:
                break
            future = self.executor.submit(self._try_login, username, password)
            futures.append(future)
            if len(futures) >= self.config.threads:
                self._wait_for_futures(futures)
                futures = []
        if futures:
            self._wait_for_futures(futures)

    def _wait_for_futures(self, futures):
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    self.success.set()
                    break
            except Exception as e:
                logging.error(f"任务执行失败: {e}")

    def _try_login(self, username: str, password: str) -> bool:
        if self.success.is_set() or self._shutdown_requested:
            return False
        try:
            resp = self._get_login_page(username, password)
            if not resp or not resp.text:
                self.stats.update("other_errors")
                return False
            token = self._extract_token(resp, username, password)
            data = self._build_login_data(username, password, token)
            resp2 = self.http.post(self.config.action, data=data)
            return self._handle_login_response(resp2, username, password)
        except RateLimitError as e:
            logging.error(f"频率限制错误: {e}")
            self.stats.update("rate_limit_errors")
            return False
        except MemoryError as e:
            logging.error(f"内存不足: {e}")
            # 内存不足时暂停任务
            time.sleep(5)
            return False
        except Exception as e:
            logging.error(f"未知错误: {e}")
            self.stats.update("other_errors")
            return False

    def _get_login_page(self, username, password):
        resp = self.http.get(self.config.url)
        analyze_form_fields(resp.text)
        return resp

    def _extract_token(self, resp, username, password):
        token = None
        if self.config.csrf:
            token = extract_token(resp.text, resp.headers.get("Content-Type", ""), self.config.csrf)
            if not token:
                logging.warning(f"未能为 {username}:{password} 提取Token（如目标无CSRF token可忽略）")
        return token

    def _build_login_data(self, username, password, token):
        data = {"username": username, "password": password}
        if self.config.csrf and token is not None:
            data[self.config.csrf] = token
        if hasattr(self.config, 'login_field') and self.config.login_field and hasattr(self.config, 'login_value'):
            data[self.config.login_field] = self.config.login_value
        return data

    def _handle_login_response(self, resp2, username, password):
        if self._check_login_success(resp2):
            logging.info(f"登录成功: {username}:{password}")
            self.stats.update("successful_attempts")
            return True
        if contains_captcha(resp2.text):
            self.stats.update("captcha_detected")
            logging.warning(f"检测到验证码: {username}:{password}")
        self.stats.update("total_attempts")
        self.state.add_attempted((username, password))
        if self.stats.stats["total_attempts"] % 100 == 0:
            self.state.save_progress(self.stats.get_stats())
        return False

    def _check_login_success(self, response, success_keywords=None, failure_keywords=None) -> bool:
        """检查登录是否成功"""
        if not response or not hasattr(response, 'text'):
            return False
        
        # 默认成功/失败关键词
        if success_keywords is None:
            success_keywords = ['welcome', 'dashboard', 'logout', 'profile', 'success', '登录成功']
        if failure_keywords is None:
            failure_keywords = ['invalid', 'incorrect', 'failed', 'error', 'login', '登录失败']
        
        response_lower = response.text.lower()
        
        # 计算成功和失败关键词的匹配数
        success_count = sum(1 for keyword in success_keywords if keyword.lower() in response_lower)
        failure_count = sum(1 for keyword in failure_keywords if keyword.lower() in response_lower)
        
        # 如果成功关键词匹配数大于失败关键词匹配数，则认为登录成功
        return success_count > failure_count
