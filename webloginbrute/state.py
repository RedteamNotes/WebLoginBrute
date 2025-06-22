#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import time
from collections import deque
from threading import RLock
from typing import Any, Dict, Set, Tuple
import hmac
import hashlib

from .exceptions import ConfigurationError
from .security import SecurityManager

SECRET_KEY = b'webloginbrute-signature-key'  # 可放到配置或环境变量

def sign_data(data: str, key=SECRET_KEY):
    return hmac.new(key, data.encode(), hashlib.sha256).hexdigest()

class StateManager:
    """
    管理程序的持久化状态，特别是已尝试的组合和进度文件的读写。
    """

    def __init__(self, config: object):
        self.config = config
        self.lock = RLock()

        # 安全地获取进度文件路径
        log_file = getattr(config, "log", "bruteforce_progress.json")
        try:
            self.progress_file = SecurityManager.get_safe_path(log_file)
        except Exception as e:
            raise ConfigurationError(f"进度文件路径不安全: {e}")

        # 使用高效的数据结构来管理已尝试的组合
        # deque 用于限制内存占用，set 用于快速查找
        self.max_in_memory_attempts = 10000
        self.attempted_combinations_deque = deque(maxlen=self.max_in_memory_attempts)
        self.attempted_combinations_set: Set[Tuple[str, str]] = set()

    def add_attempted(self, combination: Tuple[str, str]) -> None:
        """线程安全地添加一个已尝试的组合"""
        with self.lock:
            if combination not in self.attempted_combinations_set:
                # 当deque满时，从set中移除最旧的元素
                if len(self.attempted_combinations_deque) >= self.max_in_memory_attempts:
                    oldest = self.attempted_combinations_deque.popleft()
                    self.attempted_combinations_set.discard(oldest)

                self.attempted_combinations_deque.append(combination)
                self.attempted_combinations_set.add(combination)

    def has_been_attempted(self, combination: Tuple[str, str]) -> bool:
        """检查一个组合是否已经被尝试过"""
        with self.lock:
            return combination in self.attempted_combinations_set

    def load_progress(self) -> Tuple[Set[Tuple[str, str]], Dict[str, Any]]:
        """从文件加载进度，返回已尝试组合的集合和统计信息"""
        if not getattr(self.config, "resume", False):
            return set(), {}

        if not os.path.exists(self.progress_file):
            logging.info("未找到进度文件，将从头开始。")
            return set(), {}

        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                progress_data = json.load(f)

            # 恢复已尝试的组合
            loaded_attempts = set()
            if "attempted_combinations" in progress_data:
                # JSON存储的是列表，需要转换回元组
                loaded_attempts = {
                    tuple(item) for item in progress_data["attempted_combinations"]
                }

            # 将加载的组合同步到当前状态管理器
            with self.lock:
                self.attempted_combinations_set.update(loaded_attempts)
                # 更新deque，但不超过其最大长度
                for item in list(loaded_attempts)[-self.max_in_memory_attempts :]:
                    self.attempted_combinations_deque.append(item)

            logging.info(
                f"成功从 '{self.progress_file}' 恢复了 {len(loaded_attempts)} 个已尝试的组合。"
            )

            # 恢复统计信息
            stats = progress_data.get("stats", {})
            return loaded_attempts, stats

        except (json.JSONDecodeError, TypeError) as e:
            logging.warning(
                f"加载进度文件 '{self.progress_file}' 失败: {e}。将重新开始。"
            )
            return set(), {}
        except Exception as e:
            logging.exception(f"加载进度文件 '{self.progress_file}' 时发生未知异常: {e}")
            return set(), {}

    def save_progress(self, stats: Dict[str, Any]) -> None:
        """将当前进度（已尝试组合和统计信息）保存到文件"""
        with self.lock:
            # 创建要保存的数据的副本，避免在迭代时被修改
            combinations_to_save = list(self.attempted_combinations_set)

        progress_data = {
            "timestamp": time.time(),
            "attempted_combinations": combinations_to_save,
            "stats": stats,
        }

        try:
            data = json.dumps(progress_data, ensure_ascii=False)
            signature = sign_data(data)
            with open(self.progress_file, "w", encoding="utf-8") as f:
                f.write(json.dumps({'data': data, 'signature': signature}))
            logging.debug(f"进度已保存到 '{self.progress_file}'")
        except Exception as e:
            logging.exception(f"保存进度到 '{self.progress_file}' 失败: {e}")

    def cleanup_progress_file(self) -> None:
        """在任务成功完成后清理进度文件"""
        if os.path.exists(self.progress_file):
            try:
                os.remove(self.progress_file)
                logging.info(f"任务成功，进度文件 '{self.progress_file}' 已被清理。")
            except Exception as e:
                logging.exception(f"清理进度文件 '{self.progress_file}' 失败: {e}")
