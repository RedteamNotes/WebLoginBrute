#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import signal
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event
from typing import List, Optional

from .config.models import Config
from .utils.exceptions import MemoryError, HealthCheckError, ConfigurationError
from .utils.wordlists import load_wordlist_as_list
from .attack import Attack
from .services.http_client import HttpClient
from .services.state import StateManager
from .services.reporting import StatsManager
from .services.health_check import run_health_checks


class Orchestrator:
    """
    核心流程调度类，负责整体爆破流程的编排与异常处理。
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.stats = StatsManager()
        self.state = StateManager(config)
        self.http_client = HttpClient(config)
        self.attack = Attack(config, self.stats, self.http_client)

        self.users: List[str] = []
        self.passwords: List[str] = []
        self.success = Event()
        self.executor: Optional[ThreadPoolExecutor] = None
        self._shutdown_requested = False
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def run(self) -> None:
        """主运行方法"""
        logging.info("开始WebLoginBrute主流程...")
        try:
            if self.config.enable_health_check:
                run_health_checks(self.config)
            
            self._load_wordlists()
            self._setup_executor()
            self._execute_brute_force()
        except KeyboardInterrupt:
            self._handle_interruption()
        except MemoryError as e:
            self._handle_error(f"内存错误: {e}")
        except HealthCheckError as e:
            self._handle_error(f"健康检查失败: {e}")
        except ConfigurationError as e:
            self._handle_error(f"配置错误: {e}")
        except Exception as e:
            self._handle_error(f"未知的运行时错误: {e}")
        finally:
            self._cleanup_resources()

    def _signal_handler(self, signum, frame):
        logging.info(f"收到信号 {signum}，正在优雅关闭...")
        self._shutdown_requested = True
        self.success.set()
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)

    def _load_wordlists(self):
        logging.info("正在加载字典文件...")
        try:
            self.users = load_wordlist_as_list(path=self.config.users, config=self.config)
            self.passwords = load_wordlist_as_list(
                path=self.config.passwords, config=self.config
            )
            logging.info(f"成功加载 {len(self.users)} 个用户名和 {len(self.passwords)} 个密码。")
        except (FileNotFoundError, ValueError, MemoryError) as e:
            raise ConfigurationError(f"加载字典失败: {e}") from e

    def _setup_executor(self):
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.threads, thread_name_prefix="WebLoginBrute"
        )
        self.stats.stats["start_time"] = time.time()
        logging.info(f"线程池已启动，并发数: {self.config.threads}")

    def _execute_brute_force(self):
        if not self.executor:
            return
            
        total_combinations = len(self.users) * len(self.passwords)
        logging.info(f"开始暴力破解，总共 {total_combinations} 个组合")

        futures = []
        for username in self.users:
            for password in self.passwords:
                if self.success.is_set(): break
                if self.state.has_been_attempted((username, password)): continue
                
                future = self.executor.submit(self.attack.try_login, username, password)
                futures.append(future)
            if self.success.is_set(): break

        for future in as_completed(futures):
            if self.success.is_set(): break
            try:
                if future.result():
                    self.success.set()
                    logging.info("发现有效凭据！停止所有任务...")
                    break
            except Exception as e:
                logging.error(f"任务执行失败: {e}")

    def _handle_interruption(self):
        logging.info("用户中断操作，保存进度...")
        self.state.save_progress(self.stats.get_stats())

    def _handle_error(self, message: str):
        logging.error(message)
        self.state.save_progress(self.stats.get_stats())

    def _cleanup_resources(self):
        logging.info("正在清理资源...")
        if self.executor:
            self.executor.shutdown(wait=True)
        
        self.stats.finalize()
        self.stats.print_final_report(export_json=True)
        
        if self.success.is_set():
            self.state.cleanup_progress_file()
            
        self.http_client.close_all_sessions()
        logging.info("清理完成。") 