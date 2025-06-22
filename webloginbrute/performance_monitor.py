#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebLoginBrute 性能监控模块
提供全面的性能指标收集、分析和报告功能
"""

import time
import threading
import json
import statistics
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil不可用，性能监控功能将受限")

from .logger import setup_logging
from .stats import StatsCalculator


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""

    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    thread_count: int = 0
    open_files: int = 0
    network_connections: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_mb": self.memory_mb,
            "disk_io_read_mb": self.disk_io_read_mb,
            "disk_io_write_mb": self.disk_io_write_mb,
            "network_sent_mb": self.network_sent_mb,
            "network_recv_mb": self.network_recv_mb,
            "thread_count": self.thread_count,
            "open_files": self.open_files,
            "network_connections": self.network_connections,
        }


@dataclass
class OperationMetrics:
    """操作性能指标"""

    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool = True, error_message: Optional[str] = None):
        """完成操作计时"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, config=None):
        self.config = config
        self._stop_event = threading.Event()
        self._monitor_thread = None
        self._interval = 5.0  # 默认监控间隔
        self._stats_calculator: Optional[StatsCalculator] = None
        if config:
            self._interval = getattr(config, "performance_monitor_interval", 5.0)
            self._stats_calculator = StatsCalculator(config)

    def start(self):
        """启动性能监控线程"""
        if self._monitor_thread is None:
            self._monitor_thread = threading.Thread(
                target=self._run, name="PerformanceMonitor", daemon=True
            )
            self._monitor_thread.start()
            logging.info("性能监控已启动")

    def stop(self):
        """停止性能监控"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._stop_event.set()
            self._monitor_thread.join()
            logging.info("性能监控已停止")

    def track_operation(self, operation: str, success: bool, duration: float):
        """跟踪操作性能"""
        if self._stats_calculator:
            self._stats_calculator.add_operation(operation, duration, success)

    def get_summary(self) -> str:
        """获取性能摘要"""
        if self._stats_calculator:
            return self._stats_calculator.get_summary_text()
        return "性能数据不可用"

    def get_detailed_report(self) -> Dict[str, Any]:
        """获取详细的性能报告"""
        if self._stats_calculator:
            return self._stats_calculator.get_detailed_report()
        return {}

    def get_realtime_stats(self) -> Dict[str, Any]:
        """获取实时性能统计数据"""
        if self._stats_calculator:
            return self._stats_calculator.get_realtime_stats()
        return {}

    def get_summary_markdown(self) -> str:
        """获取Markdown格式的性能摘要"""
        if self._stats_calculator:
            return self._stats_calculator.get_summary_markdown()
        return "性能数据不可用"

    def _run(self):
        """性能监控后台任务"""
        while not self._stop_event.is_set():
            time.sleep(self._interval)

            if self._stats_calculator:
                # 更新统计数据
                self._stats_calculator.update_stats()

                # 记录状态
                self._stats_calculator.log_status()

                # 可以在这里添加警报逻辑，例如当RPS过低或延迟过高时
                if self._stats_calculator.current_rps < 1.0:
                    logging.warning(f"RPS过低: {self._stats_calculator.current_rps:.2f}")

                if self._stats_calculator.current_latency > 1000:
                    logging.warning(
                        f"平均延迟过高: {self._stats_calculator.current_latency:.2f} ms"
                    )


# 全局性能监控器实例
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor(config=None) -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(config)
    return _performance_monitor


def start_performance_monitoring(config=None):
    """启动性能监控的便捷函数"""
    monitor = get_performance_monitor(config)
    monitor.start()
    return monitor


def stop_performance_monitoring():
    """停止性能监控的便捷函数"""
    monitor = get_performance_monitor()
    monitor.stop()


def track_operation(operation: str, success: bool, duration: float):
    """跟踪操作性能的便捷函数"""
    monitor = get_performance_monitor()
    monitor.track_operation(operation, success, duration)


def finish_operation(
    operation: OperationMetrics,
    success: bool = True,
    error_message: Optional[str] = None,
):
    """完成操作跟踪的便捷函数"""
    monitor = get_performance_monitor()
    monitor.finish_operation(operation, success, error_message)


def get_performance_summary():
    """获取性能摘要的便捷函数"""
    monitor = get_performance_monitor()
    return monitor.get_summary()
 