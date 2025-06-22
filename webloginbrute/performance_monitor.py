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

from .logger import log_performance


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
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_mb': self.memory_mb,
            'disk_io_read_mb': self.disk_io_read_mb,
            'disk_io_write_mb': self.disk_io_write_mb,
            'network_sent_mb': self.network_sent_mb,
            'network_recv_mb': self.network_recv_mb,
            'thread_count': self.thread_count,
            'open_files': self.open_files,
            'network_connections': self.network_connections,
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
            'operation_name': self.operation_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'success': self.success,
            'error_message': self.error_message,
            'metadata': self.metadata,
        }


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, config=None):
        self.config = config
        self.lock = threading.Lock()
        self.monitoring = False
        self.monitor_thread = None
        
        # 性能指标历史
        self.metrics_history: deque = deque(maxlen=1000)  # 最多保存1000个指标点
        self.operation_history: List[OperationMetrics] = []
        
        # 监控配置
        self.monitor_interval = 5.0  # 监控间隔（秒）
        self.max_history_size = 1000
        
        # 性能阈值
        self.thresholds = {
            'cpu_warning': 80.0,
            'cpu_critical': 95.0,
            'memory_warning': 80.0,
            'memory_critical': 90.0,
            'disk_io_warning': 50.0,  # MB/s
            'network_warning': 10.0,  # MB/s
        }
        
        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # 统计信息
        self.stats = {
            'total_metrics_collected': 0,
            'total_operations_tracked': 0,
            'monitoring_start_time': None,
            'last_metrics_time': None,
        }
        
        if config:
            self._update_config_from_config()
    
    def _update_config_from_config(self):
        """从配置对象更新监控配置"""
        if hasattr(self.config, 'performance_monitor_interval'):
            self.monitor_interval = self.config.performance_monitor_interval
        
        if hasattr(self.config, 'performance_thresholds'):
            self.thresholds.update(self.config.performance_thresholds)
    
    def start_monitoring(self):
        """开始性能监控"""
        if self.monitoring:
            logging.warning("性能监控已在运行")
            return
        
        self.monitoring = True
        self.stats['monitoring_start_time'] = datetime.now()
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="PerformanceMonitor",
            daemon=True
        )
        self.monitor_thread.start()
        
        logging.info(f"性能监控已启动，监控间隔: {self.monitor_interval}秒")
    
    def stop_monitoring(self):
        """停止性能监控"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logging.info("性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self._store_metrics(metrics)
                self._check_thresholds(metrics)
                self._trigger_callbacks('metrics_collected', metrics)
                
                # 记录到日志
                log_performance(metrics.to_dict())
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logging.error(f"性能监控循环出错: {e}")
                time.sleep(self.monitor_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        metrics = PerformanceMetrics()
        
        if not PSUTIL_AVAILABLE:
            return metrics
        
        try:
            process = psutil.Process()
            
            # CPU使用率
            metrics.cpu_percent = process.cpu_percent()
            
            # 内存使用情况
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            metrics.memory_mb = memory_info.rss / 1024 / 1024
            metrics.memory_percent = memory_percent
            
            # 磁盘I/O
            try:
                io_counters = process.io_counters()
                metrics.disk_io_read_mb = io_counters.read_bytes / 1024 / 1024
                metrics.disk_io_write_mb = io_counters.write_bytes / 1024 / 1024
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
            
            # 网络I/O
            try:
                net_io = process.io_counters()
                metrics.network_sent_mb = net_io.write_bytes / 1024 / 1024
                metrics.network_recv_mb = net_io.read_bytes / 1024 / 1024
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
            
            # 线程和文件信息
            metrics.thread_count = process.num_threads()
            metrics.open_files = len(process.open_files())
            metrics.network_connections = len(process.connections())
            
        except Exception as e:
            logging.error(f"收集性能指标失败: {e}")
        
        return metrics
    
    def _store_metrics(self, metrics: PerformanceMetrics):
        """存储性能指标"""
        with self.lock:
            self.metrics_history.append(metrics)
            self.stats['total_metrics_collected'] += 1
            self.stats['last_metrics_time'] = metrics.timestamp
    
    def _check_thresholds(self, metrics: PerformanceMetrics):
        """检查性能阈值"""
        alerts = []
        
        # CPU阈值检查
        if metrics.cpu_percent > self.thresholds['cpu_critical']:
            alerts.append(('critical', 'cpu', f"CPU使用率过高: {metrics.cpu_percent:.1f}%"))
        elif metrics.cpu_percent > self.thresholds['cpu_warning']:
            alerts.append(('warning', 'cpu', f"CPU使用率较高: {metrics.cpu_percent:.1f}%"))
        
        # 内存阈值检查
        if metrics.memory_percent > self.thresholds['memory_critical']:
            alerts.append(('critical', 'memory', f"内存使用率过高: {metrics.memory_percent:.1f}%"))
        elif metrics.memory_percent > self.thresholds['memory_warning']:
            alerts.append(('warning', 'memory', f"内存使用率较高: {metrics.memory_percent:.1f}%"))
        
        # 磁盘I/O阈值检查
        if metrics.disk_io_read_mb + metrics.disk_io_write_mb > self.thresholds['disk_io_warning']:
            alerts.append(('warning', 'disk_io', f"磁盘I/O较高: {metrics.disk_io_read_mb + metrics.disk_io_write_mb:.1f}MB/s"))
        
        # 网络I/O阈值检查
        if metrics.network_sent_mb + metrics.network_recv_mb > self.thresholds['network_warning']:
            alerts.append(('warning', 'network', f"网络I/O较高: {metrics.network_sent_mb + metrics.network_recv_mb:.1f}MB/s"))
        
        # 触发告警回调
        for severity, metric_type, message in alerts:
            self._trigger_callbacks('threshold_alert', {
                'severity': severity,
                'metric_type': metric_type,
                'message': message,
                'metrics': metrics
            })
            
            if severity == 'critical':
                logging.critical(f"性能告警: {message}")
            else:
                logging.warning(f"性能告警: {message}")
    
    def track_operation(self, operation_name: str, metadata: Dict[str, Any] = None) -> OperationMetrics:
        """跟踪操作性能"""
        operation = OperationMetrics(
            operation_name=operation_name,
            start_time=datetime.now(),
            metadata=metadata or {}
        )
        
        with self.lock:
            self.operation_history.append(operation)
            self.stats['total_operations_tracked'] += 1
        
        return operation
    
    def finish_operation(self, operation: OperationMetrics, success: bool = True, 
                        error_message: Optional[str] = None):
        """完成操作跟踪"""
        operation.finish(success, error_message)
        
        # 触发操作完成回调
        self._trigger_callbacks('operation_completed', operation)
        
        # 记录操作性能
        log_performance({
            'operation_name': operation.operation_name,
            'duration': operation.duration,
            'success': operation.success,
            'metadata': operation.metadata
        })
    
    def register_callback(self, event_type: str, callback: Callable):
        """注册回调函数"""
        self.callbacks[event_type].append(callback)
    
    def _trigger_callbacks(self, event_type: str, data: Any):
        """触发回调函数"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logging.error(f"性能监控回调执行失败: {e}")
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        if not self.metrics_history:
            return None
        
        with self.lock:
            return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, minutes: int = 60) -> List[PerformanceMetrics]:
        """获取指定时间范围内的性能指标历史"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            return [
                metrics for metrics in self.metrics_history
                if metrics.timestamp > cutoff_time
            ]
    
    def get_operation_stats(self, operation_name: str = None, 
                          minutes: int = 60) -> Dict[str, Any]:
        """获取操作性能统计"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            operations = [
                op for op in self.operation_history
                if op.end_time and op.end_time > cutoff_time
            ]
            
            if operation_name:
                operations = [op for op in operations if op.operation_name == operation_name]
        
        if not operations:
            return {}
        
        # 计算统计信息
        durations = [op.duration for op in operations if op.duration is not None]
        success_count = sum(1 for op in operations if op.success)
        total_count = len(operations)
        
        stats = {
            'total_operations': total_count,
            'successful_operations': success_count,
            'failed_operations': total_count - success_count,
            'success_rate': success_count / total_count if total_count > 0 else 0,
        }
        
        if durations:
            stats.update({
                'min_duration': min(durations),
                'max_duration': max(durations),
                'avg_duration': statistics.mean(durations),
                'median_duration': statistics.median(durations),
                'std_duration': statistics.stdev(durations) if len(durations) > 1 else 0,
            })
        
        return stats
    
    def get_system_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """获取系统性能统计"""
        metrics_list = self.get_metrics_history(minutes)
        
        if not metrics_list:
            return {}
        
        # 计算统计信息
        cpu_values = [m.cpu_percent for m in metrics_list]
        memory_values = [m.memory_percent for m in metrics_list]
        memory_mb_values = [m.memory_mb for m in metrics_list]
        
        stats = {
            'monitoring_duration_minutes': minutes,
            'metrics_count': len(metrics_list),
            'cpu': {
                'current': cpu_values[-1] if cpu_values else 0,
                'average': statistics.mean(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0,
            },
            'memory': {
                'current_percent': memory_values[-1] if memory_values else 0,
                'average_percent': statistics.mean(memory_values) if memory_values else 0,
                'max_percent': max(memory_values) if memory_values else 0,
                'current_mb': memory_mb_values[-1] if memory_mb_values else 0,
                'average_mb': statistics.mean(memory_mb_values) if memory_mb_values else 0,
                'max_mb': max(memory_mb_values) if memory_mb_values else 0,
            },
        }
        
        return stats
    
    def export_report(self, file_path: str = None) -> str:
        """导出性能报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'monitor_stats': self.stats,
            'system_stats': self.get_system_stats(),
            'operation_stats': self.get_operation_stats(),
            'recent_metrics': [
                metrics.to_dict() for metrics in list(self.metrics_history)[-100:]
            ],
            'recent_operations': [
                op.to_dict() for op in self.operation_history[-100:]
            ],
            'thresholds': self.thresholds,
        }
        
        report_json = json.dumps(report, ensure_ascii=False, indent=2)
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_json)
                logging.info(f"性能报告已导出到: {file_path}")
            except Exception as e:
                logging.error(f"导出性能报告失败: {e}")
        
        return report_json
    
    def print_summary(self):
        """打印性能摘要"""
        current_metrics = self.get_current_metrics()
        system_stats = self.get_system_stats()
        operation_stats = self.get_operation_stats()
        
        print("\n" + "=" * 60)
        print("                   性能监控摘要")
        print("=" * 60)
        
        if current_metrics:
            print(f"\n当前性能指标:")
            print(f"  CPU使用率: {current_metrics.cpu_percent:.1f}%")
            print(f"  内存使用率: {current_metrics.memory_percent:.1f}% ({current_metrics.memory_mb:.1f}MB)")
            print(f"  线程数: {current_metrics.thread_count}")
            print(f"  打开文件数: {current_metrics.open_files}")
            print(f"  网络连接数: {current_metrics.network_connections}")
        
        if system_stats:
            print(f"\n系统性能统计 (最近{system_stats.get('monitoring_duration_minutes', 0)}分钟):")
            print(f"  收集指标数: {system_stats.get('metrics_count', 0)}")
            print(f"  CPU平均使用率: {system_stats.get('cpu', {}).get('average', 0):.1f}%")
            print(f"  内存平均使用率: {system_stats.get('memory', {}).get('average_percent', 0):.1f}%")
        
        if operation_stats:
            print(f"\n操作性能统计:")
            print(f"  总操作数: {operation_stats.get('total_operations', 0)}")
            print(f"  成功率: {operation_stats.get('success_rate', 0):.2%}")
            if 'avg_duration' in operation_stats:
                print(f"  平均耗时: {operation_stats['avg_duration']:.3f}秒")
        
        print("=" * 60)


# 全局性能监控器实例
_performance_monitor = None


def get_performance_monitor(config=None) -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(config)
    return _performance_monitor


def start_performance_monitoring(config=None):
    """启动性能监控的便捷函数"""
    monitor = get_performance_monitor(config)
    monitor.start_monitoring()
    return monitor


def stop_performance_monitoring():
    """停止性能监控的便捷函数"""
    monitor = get_performance_monitor()
    monitor.stop_monitoring()


def track_operation(operation_name: str, metadata: Dict[str, Any] = None) -> OperationMetrics:
    """跟踪操作的便捷函数"""
    monitor = get_performance_monitor()
    return monitor.track_operation(operation_name, metadata)


def finish_operation(operation: OperationMetrics, success: bool = True, 
                    error_message: Optional[str] = None):
    """完成操作跟踪的便捷函数"""
    monitor = get_performance_monitor()
    monitor.finish_operation(operation, success, error_message)


def get_performance_summary():
    """获取性能摘要的便捷函数"""
    monitor = get_performance_monitor()
    return monitor.get_system_stats() 