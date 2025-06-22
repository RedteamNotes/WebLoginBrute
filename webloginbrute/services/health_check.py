#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebLoginBrute 系统健康检查模块
提供全面的系统状态监控、性能指标收集和问题诊断功能
"""

import logging
import time
import threading
import socket
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse
import json
from typing import Dict, Any, List, Callable, Union, Optional

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil不可用，系统监控功能将受限")

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..config.models import Config
from ..utils.exceptions import HealthCheckError
from ..logger import setup_logging

log = setup_logging()


@dataclass
class HealthCheckResult:
    """健康检查结果"""

    check_name: str
    status: str  # 'PASS', 'WARNING', 'FAIL', 'UNKNOWN'
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "check_name": self.check_name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
        }


@dataclass
class SystemMetrics:
    """系统指标"""

    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_available: float = 0.0
    disk_usage: float = 0.0
    disk_free: float = 0.0
    network_connections: int = 0
    open_files: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "memory_available": self.memory_available,
            "disk_usage": self.disk_usage,
            "disk_free": self.disk_free,
            "network_connections": self.network_connections,
            "open_files": self.open_files,
            "timestamp": self.timestamp.isoformat(),
        }


class HealthChecker:
    """系统健康检查器"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config
        self.lock = threading.Lock()
        self.check_results: List[HealthCheckResult] = []
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 100
        self.check_callbacks: Dict[str, List[Callable]] = {}
        self.network_checks: List[Callable[[], bool]] = []
        self.system_checks: List[
            Callable[[], Union[HealthCheckResult, List[HealthCheckResult]]]
        ] = []
        self.file_checks: List[Callable[[], bool]] = []

        # 性能阈值
        self.thresholds = {
            "cpu_warning": 80.0,  # CPU使用率警告阈值
            "cpu_critical": 95.0,  # CPU使用率临界阈值
            "memory_warning": 80.0,  # 内存使用率警告阈值
            "memory_critical": 90.0,  # 内存使用率临界阈值
            "disk_warning": 85.0,  # 磁盘使用率警告阈值
            "disk_critical": 95.0,  # 磁盘使用率临界阈值
            "response_time_warning": 5.0,  # 响应时间警告阈值(秒)
            "response_time_critical": 10.0,  # 响应时间临界阈值(秒)
        }

        if self.config:
            # 从配置中更新阈值
            self.thresholds.update(
                {
                    "memory_warning": getattr(config, "memory_warning_threshold", 0.8)
                    * 100,
                    "memory_critical": getattr(config, "memory_critical_threshold", 0.9)
                    * 100,
                }
            )

        self._register_checks()

    def _register_checks(self):
        """注册所有健康检查"""
        self.system_checks = [
            self.check_system_resources,
            self.check_network_connectivity,
            self.check_memory_usage,
            self.check_disk_space,
            self.check_process_health,
            self.check_network_performance,
        ]

    def register_check_callback(self, check_name: str, callback: Callable):
        """注册检查回调函数"""
        if check_name not in self.check_callbacks:
            self.check_callbacks[check_name] = []
        self.check_callbacks[check_name].append(callback)

    def run_all_checks(self) -> List[HealthCheckResult]:
        """运行所有健康检查"""
        logging.info("开始执行系统健康检查...")

        results = []
        with ThreadPoolExecutor(max_workers=len(self.system_checks)) as executor:
            future_to_check = {
                executor.submit(check_func): check_func for check_func in self.system_checks
            }
            for future in as_completed(future_to_check):
                check_func = future_to_check[future]
                try:
                    result = future.result()
                    if isinstance(result, list):
                        results.extend(result)
                    else:
                        results.append(result)
                except Exception as e:
                    logging.error(f"健康检查失败 {check_func.__name__}: {e}")
                    results.append(
                        HealthCheckResult(
                            check_name=check_func.__name__,
                            status="FAIL",
                            message=f"检查执行失败: {e}",
                            details={"error": str(e)},
                        )
                    )

        # 保存结果
        with self.lock:
            self.check_results.extend(results)
            # 保持历史记录在合理范围内
            if len(self.check_results) > self.max_history_size:
                self.check_results = self.check_results[-self.max_history_size :]

        # 触发回调
        self._trigger_callbacks(results)

        logging.info(f"健康检查完成，共执行 {len(results)} 项检查")
        return results

    def run_all_sequential(self) -> List[HealthCheckResult]:
        """按顺序运行所有检查（用于调试或简单场景）"""
        results = []
        for check_func in self.system_checks:
            try:
                result = check_func()
                if isinstance(result, list):
                    results.extend(result)
                else:
                    results.append(result)
            except Exception as e:
                logging.error(f"健康检查失败 {check_func.__name__}: {e}")
                results.append(
                    HealthCheckResult(
                        check_name=check_func.__name__,
                        status="FAIL",
                        message=f"检查执行失败: {e}",
                        details={"error": str(e)},
                    )
                )
        return results

    def check_system_resources(self) -> HealthCheckResult:
        """检查系统资源"""
        start_time = time.time()

        if not PSUTIL_AVAILABLE:
            return HealthCheckResult(
                check_name="system_resources",
                status="UNKNOWN",
                message="psutil不可用，无法检查系统资源",
                details={"psutil_available": False},
            )

        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / 1024 / 1024

            # 磁盘使用情况
            disk = psutil.disk_usage(".")
            disk_percent = (disk.used / disk.total) * 100
            disk_free_mb = disk.free / 1024 / 1024

            # 网络连接数
            network_connections = len(psutil.net_connections())

            # 打开文件数
            open_files = len(psutil.Process().open_files())

            # 判断状态
            status = "PASS"
            message = "系统资源正常"

            if cpu_percent > self.thresholds["cpu_critical"]:
                status = "FAIL"
                message = f"CPU使用率过高: {cpu_percent:.1f}%"
            elif cpu_percent > self.thresholds["cpu_warning"]:
                status = "WARNING"
                message = f"CPU使用率较高: {cpu_percent:.1f}%"

            if memory_percent > self.thresholds["memory_critical"]:
                status = "FAIL"
                message = f"内存使用率过高: {memory_percent:.1f}%"
            elif memory_percent > self.thresholds["memory_warning"]:
                status = "WARNING"
                message = f"内存使用率较高: {memory_percent:.1f}%"

            if disk_percent > self.thresholds["disk_critical"]:
                status = "FAIL"
                message = f"磁盘使用率过高: {disk_percent:.1f}%"
            elif disk_percent > self.thresholds["disk_warning"]:
                status = "WARNING"
                message = f"磁盘使用率较高: {disk_percent:.1f}%"

            duration = time.time() - start_time

            return HealthCheckResult(
                check_name="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_available_mb": memory_available_mb,
                    "disk_percent": disk_percent,
                    "disk_free_mb": disk_free_mb,
                    "network_connections": network_connections,
                    "open_files": open_files,
                },
                duration=duration,
            )

        except Exception as e:
            return HealthCheckResult(
                check_name="system_resources",
                status="FAIL",
                message=f"系统资源检查失败: {e}",
                details={"error": str(e)},
                duration=time.time() - start_time,
            )

    def check_network_connectivity(self) -> List[HealthCheckResult]:
        """检查网络连通性"""
        start_time = time.time()
        results = []

        if not self.config or not self.config.url:
            results.append(
                HealthCheckResult(
                    check_name="network_connectivity",
                    status="UNKNOWN",
                    message="配置或URL不可用，无法检查网络连通性",
                )
            )
            return results

        # 检查DNS解析
        target_host = urlparse(self.config.url).hostname
        if not target_host:
            results.append(
                HealthCheckResult(
                    check_name="dns_resolution",
                    status="FAIL",
                    message="无法从URL中解析主机名",
                    details={"url": self.config.url},
                )
            )
            return results

        try:
            ip_address = socket.gethostbyname(target_host)
            results.append(
                HealthCheckResult(
                    check_name="dns_resolution",
                    status="PASS",
                    message=f"DNS解析成功: {target_host} -> {ip_address}",
                    details={"host": target_host, "ip_address": ip_address},
                    duration=time.time() - start_time,
                )
            )
        except socket.gaierror as e:
            results.append(
                HealthCheckResult(
                    check_name="dns_resolution",
                    status="FAIL",
                    message=f"DNS解析失败: {target_host}",
                    details={"host": target_host, "error": str(e)},
                    duration=time.time() - start_time,
                )
            )
            return results  # DNS失败，后续检查无意义

        # 检查网络延迟
        ping_start_time = time.time()
        try:
            sock = socket.create_connection((target_host, 80), timeout=5)
            sock.close()
            latency = (time.time() - ping_start_time) * 1000  # 毫秒
            results.append(
                HealthCheckResult(
                    check_name="network_latency",
                    status="PASS",
                    message=f"网络延迟正常: {latency:.2f} ms",
                    details={"latency_ms": latency},
                    duration=time.time() - ping_start_time,
                )
            )
        except (socket.timeout, ConnectionRefusedError) as e:
            results.append(
                HealthCheckResult(
                    check_name="network_latency",
                    status="FAIL",
                    message="网络连接超时或被拒绝",
                    details={"error": str(e)},
                    duration=time.time() - ping_start_time,
                )
            )

        # 检查目标URL可访问性
        try:
            # 延迟导入以避免循环依赖
            from .http_client import HttpClient
            client = HttpClient(self.config)
            client.get(self.config.url)
            results.append(
                HealthCheckResult(
                    check_name="url_accessibility",
                    status="PASS",
                    message="目标URL可访问",
                    duration=time.time() - start_time,
                )
            )
        except Exception as e:
            results.append(
                HealthCheckResult(
                    check_name="url_accessibility",
                    status="FAIL",
                    message=f"目标URL访问失败: {e}",
                    duration=time.time() - start_time,
                )
            )

        return results

    def check_memory_usage(self) -> HealthCheckResult:
        """检查内存使用情况"""
        start_time = time.time()

        if not PSUTIL_AVAILABLE:
            return HealthCheckResult(
                check_name="memory_usage",
                status="UNKNOWN",
                message="psutil不可用，无法检查内存使用情况",
            )

        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / 1024 / 1024
            memory_total_mb = memory.total / 1024 / 1024

            # 检查当前进程内存使用
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / 1024 / 1024

            status = "PASS"
            message = "内存使用正常"

            if memory_percent > self.thresholds["memory_critical"]:
                status = "FAIL"
                message = f"内存使用率过高: {memory_percent:.1f}%"
            elif memory_percent > self.thresholds["memory_warning"]:
                status = "WARNING"
                message = f"内存使用率较高: {memory_percent:.1f}%"

            # 记录指标
            metrics = SystemMetrics(
                cpu_usage=psutil.cpu_percent(),
                memory_usage=memory_percent,
                memory_available=memory_available_mb,
                disk_usage=(psutil.disk_usage(".").used / psutil.disk_usage(".").total)
                * 100,
                disk_free=psutil.disk_usage(".").free / 1024 / 1024,
                network_connections=len(psutil.net_connections()),
                open_files=len(process.open_files()),
            )

            with self.lock:
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history = self.metrics_history[
                        -self.max_history_size :
                    ]

            return HealthCheckResult(
                check_name="memory_usage",
                status=status,
                message=message,
                details={
                    "memory_percent": memory_percent,
                    "memory_available_mb": memory_available_mb,
                    "memory_total_mb": memory_total_mb,
                    "process_memory_mb": process_memory_mb,
                },
                duration=time.time() - start_time,
            )

        except Exception as e:
            return HealthCheckResult(
                check_name="memory_usage",
                status="FAIL",
                message=f"内存使用检查失败: {e}",
                details={"error": str(e)},
                duration=time.time() - start_time,
            )

    def check_disk_space(self) -> HealthCheckResult:
        """检查磁盘空间"""
        start_time = time.time()

        if not PSUTIL_AVAILABLE:
            return HealthCheckResult(
                check_name="disk_space",
                status="UNKNOWN",
                message="psutil不可用，无法检查磁盘空间",
            )

        try:
            disk = psutil.disk_usage(".")
            disk_percent = (disk.used / disk.total) * 100
            disk_free_mb = disk.free / 1024 / 1024
            disk_total_mb = disk.total / 1024 / 1024

            status = "PASS"
            message = "磁盘空间充足"

            if disk_percent > self.thresholds["disk_critical"]:
                status = "FAIL"
                message = f"磁盘空间严重不足: {disk_percent:.1f}%"
            elif disk_percent > self.thresholds["disk_warning"]:
                status = "WARNING"
                message = f"磁盘空间不足: {disk_percent:.1f}%"

            return HealthCheckResult(
                check_name="disk_space",
                status=status,
                message=message,
                details={
                    "disk_percent": disk_percent,
                    "disk_free_mb": disk_free_mb,
                    "disk_total_mb": disk_total_mb,
                },
                duration=time.time() - start_time,
            )

        except Exception as e:
            return HealthCheckResult(
                check_name="disk_space",
                status="FAIL",
                message=f"磁盘空间检查失败: {e}",
                details={"error": str(e)},
                duration=time.time() - start_time,
            )

    def check_process_health(self) -> HealthCheckResult:
        """检查进程健康状态"""
        start_time = time.time()

        if not PSUTIL_AVAILABLE:
            return HealthCheckResult(
                check_name="process_health",
                status="UNKNOWN",
                message="psutil不可用，无法检查进程健康状态",
            )

        try:
            process = psutil.Process()

            # 检查进程状态
            status_info = process.status()
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # 检查线程数
            thread_count = process.num_threads()

            # 检查打开的文件数
            open_files_count = len(process.open_files())

            # 检查网络连接数
            network_connections_count = len(process.connections())

            status = "PASS"
            message = "进程健康状态正常"

            # 检查进程是否响应
            if status_info == psutil.STATUS_ZOMBIE:
                status = "FAIL"
                message = "进程处于僵尸状态"
            elif status_info == psutil.STATUS_STOPPED:
                status = "FAIL"
                message = "进程已停止"

            # 检查资源使用是否异常
            if cpu_percent > 90:
                status = "WARNING"
                message = f"进程CPU使用率过高: {cpu_percent:.1f}%"

            if memory_mb > 1000:  # 超过1GB
                status = "WARNING"
                message = f"进程内存使用过高: {memory_mb:.1f}MB"

            return HealthCheckResult(
                check_name="process_health",
                status=status,
                message=message,
                details={
                    "status": status_info,
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_mb,
                    "thread_count": thread_count,
                    "open_files_count": open_files_count,
                    "network_connections_count": network_connections_count,
                },
                duration=time.time() - start_time,
            )

        except Exception as e:
            return HealthCheckResult(
                check_name="process_health",
                status="FAIL",
                message=f"进程健康检查失败: {e}",
                details={"error": str(e)},
                duration=time.time() - start_time,
            )

    def check_network_performance(self) -> HealthCheckResult:
        """检查网络性能"""
        start_time = time.time()

        if not self.config:
            return HealthCheckResult(
                check_name="network_performance",
                status="UNKNOWN",
                message="配置不可用，无法检查网络性能",
            )

        try:
            # 测试网络延迟
            test_url = self.config.url
            response_times = []

            for i in range(3):  # 测试3次取平均值
                try:
                    req_start = time.time()
                    response = requests.head(test_url, timeout=10, allow_redirects=True)
                    req_time = time.time() - req_start
                    response_times.append(req_time)
                except Exception as e:
                    logging.warning(f"网络性能测试失败 (尝试 {i + 1}): {e}")

            if not response_times:
                return HealthCheckResult(
                    check_name="network_performance",
                    status="FAIL",
                    message="网络性能测试失败",
                    details={"error": "所有测试请求都失败"},
                    duration=time.time() - start_time,
                )

            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)

            status = "PASS"
            message = f"网络性能正常，平均响应时间: {avg_response_time:.3f}s"

            if avg_response_time > self.thresholds["response_time_critical"]:
                status = "FAIL"
                message = f"网络响应时间过长: {avg_response_time:.3f}s"
            elif avg_response_time > self.thresholds["response_time_warning"]:
                status = "WARNING"
                message = f"网络响应时间较慢: {avg_response_time:.3f}s"

            return HealthCheckResult(
                check_name="network_performance",
                status=status,
                message=message,
                details={
                    "avg_response_time": avg_response_time,
                    "min_response_time": min_response_time,
                    "max_response_time": max_response_time,
                    "test_count": len(response_times),
                    "test_url": test_url,
                },
                duration=time.time() - start_time,
            )

        except Exception as e:
            return HealthCheckResult(
                check_name="network_performance",
                status="FAIL",
                message=f"网络性能检查失败: {e}",
                details={"error": str(e)},
                duration=time.time() - start_time,
            )

    def _trigger_callbacks(self, results: List[HealthCheckResult]):
        """触发检查回调函数"""
        for result in results:
            if result.check_name in self.check_callbacks:
                for callback in self.check_callbacks[result.check_name]:
                    try:
                        callback(result)
                    except Exception as e:
                        logging.error(f"健康检查回调执行失败: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """获取健康检查摘要"""
        with self.lock:
            if not self.check_results:
                return {"status": "UNKNOWN", "message": "暂无健康检查结果"}

            # 统计各状态数量
            status_counts = {}
            for result in self.check_results:
                status_counts[result.status] = status_counts.get(result.status, 0) + 1

            # 获取最新结果
            latest_results = self.check_results[-10:]  # 最近10个结果

            # 确定整体状态
            if status_counts.get("FAIL", 0) > 0:
                overall_status = "FAIL"
                message = f'发现 {status_counts["FAIL"]} 个失败项'
            elif status_counts.get("WARNING", 0) > 0:
                overall_status = "WARNING"
                message = f'发现 {status_counts["WARNING"]} 个警告项'
            else:
                overall_status = "PASS"
                message = "所有检查项正常"

            return {
                "overall_status": overall_status,
                "message": message,
                "status_counts": status_counts,
                "total_checks": len(self.check_results),
                "latest_results": [result.to_dict() for result in latest_results],
                "last_check_time": (
                    self.check_results[-1].timestamp.isoformat()
                    if self.check_results
                    else None
                ),
            }

    def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """获取指定时间范围内的指标历史"""
        with self.lock:
            if not self.metrics_history:
                return []

            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [
                metrics
                for metrics in self.metrics_history
                if metrics.timestamp > cutoff_time
            ]

            return [metrics.to_dict() for metrics in recent_metrics]

    def export_report(self, file_path: Optional[str] = None) -> str:
        """
        导出健康检查报告为JSON文件。
        :param file_path: 报告文件路径。如果为None，则自动生成文件名。
        :return: 报告文件的实际路径。
        """
        report_data = self._get_final_report()
        
        if file_path is None:
            file_path = f"health_report_{int(time.time())}.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)
            logging.info(f"健康检查报告已导出到: {file_path}")
            return file_path
        except IOError as e:
            logging.error(f"导出健康检查报告失败: {e}")
            raise HealthCheckError(f"无法写入报告文件: {file_path}") from e

    def _get_final_report(self) -> Dict[str, Any]:
        summary = self.get_summary()
        return {
            "report_generated_at": datetime.now().isoformat(),
            "summary": summary,
            "checks": [result.to_dict() for result in self.check_results],
        }


# 全局健康检查器实例
_health_checker_instance: Optional[HealthChecker] = None


def get_health_checker(config: Optional[Config] = None) -> HealthChecker:
    """获取健康检查器单例"""
    global _health_checker_instance
    if _health_checker_instance is None:
        _health_checker_instance = HealthChecker(config)
    return _health_checker_instance


def run_health_checks(config: Optional[Config] = None) -> List[HealthCheckResult]:
    """运行健康检查并返回结果"""
    checker = get_health_checker(config)
    return checker.run_all_checks()


def get_health_summary() -> Optional[Dict[str, Any]]:
    """获取健康检查摘要"""
    checker = get_health_checker()
    if checker:
        return checker.get_summary()
    return None
 