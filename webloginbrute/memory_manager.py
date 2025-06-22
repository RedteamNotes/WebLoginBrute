#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebLoginBrute 内存管理模块
提供严格的内存使用限制、监控和清理功能
"""

import logging
import time
import gc
from typing import Optional, Dict, Any, Callable
from threading import Lock, Timer
from dataclasses import dataclass
from contextlib import contextmanager

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil未安装，内存监控功能将受限")


@dataclass
class MemoryConfig:
    """内存配置"""
    max_memory_mb: int = 500  # 最大内存使用量(MB)
    warning_threshold: float = 0.8  # 警告阈值(80%)
    critical_threshold: float = 0.9  # 临界阈值(90%)
    cleanup_interval: int = 60  # 清理间隔(秒)
    gc_threshold: int = 100  # 垃圾回收阈值(MB)


class MemoryManager:
    """内存管理器"""
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.lock = Lock()
        self._last_cleanup = time.time()
        self._memory_history = []
        self._cleanup_callbacks = []
        self._monitoring = False
        self._monitor_timer = None
        
        # 内存使用统计
        self.stats = {
            'peak_memory': 0,
            'cleanup_count': 0,
            'gc_count': 0,
            'warning_count': 0,
            'critical_count': 0,
            'last_check': time.time()
        }
        
        if not PSUTIL_AVAILABLE:
            logging.warning("psutil不可用，内存监控功能受限")
    
    def start_monitoring(self):
        """开始内存监控"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._schedule_next_check()
        logging.info("内存监控已启动")
    
    def stop_monitoring(self):
        """停止内存监控"""
        self._monitoring = False
        if self._monitor_timer:
            self._monitor_timer.cancel()
            self._monitor_timer = None
        logging.info("内存监控已停止")
    
    def _schedule_next_check(self):
        """安排下一次检查"""
        if not self._monitoring:
            return
        
        self._monitor_timer = Timer(self.config.cleanup_interval, self._check_memory)
        self._monitor_timer.daemon = True
        self._monitor_timer.start()
    
    def _check_memory(self):
        """检查内存使用情况"""
        try:
            current_memory = self.get_current_memory()
            if current_memory is None:
                return
            
            with self.lock:
                self.stats['last_check'] = time.time()
                
                # 更新峰值内存
                if current_memory > self.stats['peak_memory']:
                    self.stats['peak_memory'] = current_memory
                
                # 记录内存历史
                self._memory_history.append({
                    'timestamp': time.time(),
                    'memory_mb': current_memory
                })
                
                # 保持历史记录在合理范围内
                if len(self._memory_history) > 100:
                    self._memory_history = self._memory_history[-50:]
                
                # 检查阈值
                memory_ratio = current_memory / self.config.max_memory_mb
                
                if memory_ratio >= self.config.critical_threshold:
                    self.stats['critical_count'] += 1
                    logging.critical(f"内存使用达到临界值: {current_memory:.1f}MB ({memory_ratio:.1%})")
                    self._emergency_cleanup()
                elif memory_ratio >= self.config.warning_threshold:
                    self.stats['warning_count'] += 1
                    logging.warning(f"内存使用较高: {current_memory:.1f}MB ({memory_ratio:.1%})")
                    self._normal_cleanup()
                elif current_memory > self.config.gc_threshold:
                    # 定期垃圾回收
                    self._garbage_collection()
            
        except Exception as e:
            logging.error(f"内存检查失败: {e}")
        finally:
            # 安排下一次检查
            self._schedule_next_check()
    
    def get_current_memory(self) -> Optional[float]:
        """获取当前内存使用量(MB)"""
        if not PSUTIL_AVAILABLE:
            return None
        
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # 转换为MB
        except Exception as e:
            logging.debug(f"获取内存使用量失败: {e}")
            return None
    
    def _normal_cleanup(self):
        """正常清理"""
        with self.lock:
            self.stats['cleanup_count'] += 1
        
        # 执行清理回调
        for callback in self._cleanup_callbacks:
            try:
                callback('normal')
            except Exception as e:
                logging.error(f"执行清理回调失败: {e}")
        
        # 强制垃圾回收
        self._garbage_collection()
        
        logging.debug("执行正常内存清理")
    
    def _emergency_cleanup(self):
        """紧急清理"""
        with self.lock:
            self.stats['cleanup_count'] += 1
        
        # 执行紧急清理回调
        for callback in self._cleanup_callbacks:
            try:
                callback('emergency')
            except Exception as e:
                logging.error(f"执行紧急清理回调失败: {e}")
        
        # 强制垃圾回收
        self._garbage_collection()
        
        # 清理内存历史
        self._memory_history.clear()
        
        logging.warning("执行紧急内存清理")
    
    def _garbage_collection(self):
        """垃圾回收"""
        with self.lock:
            self.stats['gc_count'] += 1
        
        # 强制垃圾回收
        collected = gc.collect()
        logging.debug(f"垃圾回收完成，回收对象数: {collected}")
    
    def add_cleanup_callback(self, callback: Callable[[str], None]):
        """添加清理回调函数"""
        self._cleanup_callbacks.append(callback)
    
    def remove_cleanup_callback(self, callback: Callable[[str], None]):
        """移除清理回调函数"""
        if callback in self._cleanup_callbacks:
            self._cleanup_callbacks.remove(callback)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        current_memory = self.get_current_memory()
        
        with self.lock:
            stats = self.stats.copy()
            stats['current_memory'] = current_memory
            stats['memory_ratio'] = current_memory / self.config.max_memory_mb if current_memory else 0
            stats['history_count'] = len(self._memory_history)
        
        return stats
    
    def check_memory_limit(self, required_mb: float = 0) -> bool:
        """检查是否超过内存限制"""
        current_memory = self.get_current_memory()
        if current_memory is None:
            return True  # 无法检测时允许继续
        
        total_required = current_memory + required_mb
        return total_required <= self.config.max_memory_mb
    
    @contextmanager
    def memory_context(self, required_mb: float = 0):
        """内存上下文管理器"""
        current_memory = self.get_current_memory()
        if current_memory is not None and not self.check_memory_limit(required_mb):
            available_memory = self.config.max_memory_mb - current_memory
            raise MemoryError(f"内存不足，需要{required_mb}MB，当前可用{available_memory:.1f}MB")
        
        try:
            yield
        finally:
            # 上下文结束时检查内存
            self._check_memory()
    
    def cleanup(self):
        """清理资源"""
        self.stop_monitoring()
        self._cleanup_callbacks.clear()
        self._memory_history.clear()
        self._garbage_collection()


# 全局内存管理器实例
_global_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """获取全局内存管理器"""
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager()
    return _global_memory_manager


def init_memory_manager(config: Optional[MemoryConfig] = None) -> MemoryManager:
    """初始化内存管理器"""
    global _global_memory_manager
    if _global_memory_manager:
        _global_memory_manager.cleanup()
    
    _global_memory_manager = MemoryManager(config)
    return _global_memory_manager 