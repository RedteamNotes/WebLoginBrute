#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
from threading import Lock
from typing import Any, Dict

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class StatsManager:
    """
    线程安全地管理和报告所有统计数据和性能指标。
    """

    def __init__(self):
        self.lock = Lock()

        self.stats: Dict[str, Any] = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "timeout_errors": 0,
            "connection_errors": 0,
            "http_errors": 0,
            "other_errors": 0,
            "retry_attempts": 0,
            "rate_limited": 0,
            "captcha_detected": 0,
            "start_time": time.time(),
            "end_time": None,
        }

        self.performance: Dict[str, Any] = {
            "peak_memory_usage": 0,
            "avg_response_time": 0,
            "total_response_time": 0,
            "response_count": 0,
            "memory_cleanup_count": 0,
        }

        self._initial_memory = self.get_current_memory()

    def update(self, stat_type: str, value: int = 1):
        """线程安全地更新一个统计项"""
        with self.lock:
            if stat_type in self.stats:
                self.stats[stat_type] += value
            else:
                logging.warning(f"尝试更新未知的统计类型: {stat_type}")

    def get_stats(self) -> Dict[str, Any]:
        """获取当前统计信息的一个副本"""
        with self.lock:
            return self.stats.copy()

    def update_from_progress(self, progress_stats: Dict[str, Any]):
        """从加载的进度文件中恢复统计信息"""
        with self.lock:
            # 只更新存在的键，避免随意添加
            for key, value in progress_stats.items():
                if key in self.stats:
                    self.stats[key] = value
            logging.info("已从进度文件中恢复统计信息")

    def record_response_time(self, response_time: float):
        """记录一次响应时间并更新平均值"""
        with self.lock:
            self.performance["total_response_time"] += response_time
            self.performance["response_count"] += 1
            if self.performance["response_count"] > 0:
                self.performance["avg_response_time"] = (
                    self.performance["total_response_time"]
                    / self.performance["response_count"]
                )

    def check_peak_memory(self):
        """检查并更新峰值内存使用"""
        current_memory = self.get_current_memory()
        if current_memory is None:
            return

        with self.lock:
            if current_memory > self.performance["peak_memory_usage"]:
                self.performance["peak_memory_usage"] = current_memory

    def get_current_memory(self) -> float | None:
        """获取当前进程的内存使用情况（MB）"""
        if not PSUTIL_AVAILABLE:
            return None
        try:
            process = psutil.Process()
            # 使用RSS（Resident Set Size）作为内存占用的衡量标准
            return process.memory_info().rss / 1024 / 1024
        except psutil.NoSuchProcess:
            return None

    def finalize(self):
        """完成统计，记录结束时间并计算最终指标"""
        with self.lock:
            if self.stats["end_time"] is None:
                self.stats["end_time"] = time.time()
        self.check_peak_memory()
        logging.info("统计管理器已终结。")

    def print_final_report(self):
        """打印格式化的最终统计报告"""
        with self.lock:
            if self.stats["start_time"] is None or self.stats["end_time"] is None:
                print("\n[!] 任务未正确开始或结束，无法生成报告。")
                return

            duration = self.stats["end_time"] - self.stats["start_time"]

            # 避免除以零
            avg_rate = (
                self.stats["total_attempts"] / duration if duration > 0 else 0
            )

            print("\n" + "=" * 50)
            print("                暴力破解任务完成")
            print("=" * 50)
            print(" 概要信息")
            print(f"   - 总耗时: {duration:.2f} 秒")
            print(f"   - 总尝试次数: {self.stats['total_attempts']}")
            print(f"   - 平均速率: {avg_rate:.2f} 次/秒")
            print("-" * 50)
            print(" 结果分析")
            print(f"   - 成功破解: {self.stats['successful_attempts']}")
            print(f"   - 遭遇频率限制: {self.stats['rate_limited']}")
            print(f"   - 检测到验证码: {self.stats['captcha_detected']}")
            print("-" * 50)
            print(" 错误统计")
            print(f"   - 超时错误: {self.stats['timeout_errors']}")
            print(f"   - 连接错误: {self.stats['connection_errors']}")
            print(f"   - HTTP错误: {self.stats['http_errors']}")
            print(f"   - 其他错误: {self.stats['other_errors']}")
            print(f"   - 内部重试: {self.stats['retry_attempts']}")
            print("-" * 50)
            print(" 性能指标")
            print(f"   - 平均响应时间: {self.performance['avg_response_time']:.3f} 秒")
            print(f"   - 峰值内存使用: {self.performance['peak_memory_usage']:.1f} MB")
            print("=" * 50)
