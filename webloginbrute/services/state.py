#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import time
import threading
from typing import Tuple, Dict, Any, Set

from ..config.models import Config
from ..utils.exceptions import ConfigurationError
# SecurityManager is no longer used directly for path validation here
# from .security import SecurityManager

class StateManager:
    """
    管理程序的持久化状态，特别是已尝试的组合和进度文件的读写。
    """

    def __init__(self, config: Config):
        self.config = config
        self.lock = threading.RLock()
        self.progress_file: str | None = None
        
        log_file_path = getattr(config, "log", None)

        if log_file_path:
             # Basic path validation, more advanced checks are in SecurityManager
             if not isinstance(log_file_path, str) or not log_file_path.strip():
                 raise ConfigurationError("Log file path must be a non-empty string.")
             self.progress_file = os.path.abspath(log_file_path)
        
        # _state 包含所有需要持久化的数据
        self._state: Dict[str, Any] = {
            "attempted_credentials": set(),
            "stats": {}
        }

        if config.resume:
            self.load_progress()

    def load_progress(self):
        """从文件加载进度，并更新内部状态。"""
        if not self.progress_file or not os.path.exists(self.progress_file):
            logging.info("未找到进度文件或未指定，将从头开始。")
            return

        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                progress_data = json.load(f)

            loaded_creds = progress_data.get("attempted_credentials", [])
            self._state["attempted_credentials"] = {tuple(cred) for cred in loaded_creds}
            self._state["stats"] = progress_data.get("stats", {})

            logging.info(
                f"成功从 '{self.progress_file}' 恢复了 "
                f"{len(self._state['attempted_credentials'])} 个已尝试的组合。"
            )

        except (json.JSONDecodeError, TypeError) as e:
            logging.warning(
                f"加载进度文件 '{self.progress_file}' 失败: {e}。将重新开始。"
            )

    def save_progress(self, stats: Dict[str, Any]):
        """将当前进度（已尝试组合和统计信息）保存到文件"""
        if not self.progress_file:
            return

        with self.lock:
            # 创建要保存的数据的副本
            data_to_save = {
                "timestamp": time.time(),
                "stats": stats,
                # 将凭据的set转换为list以便JSON序列化
                "attempted_credentials": list(self._state["attempted_credentials"]),
            }

        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=4)
            logging.debug(f"进度已保存到 '{self.progress_file}'")
        except IOError as e:
            logging.error(f"保存进度到 '{self.progress_file}' 失败: {e}")

    def has_been_attempted(self, combination: Tuple[str, str]) -> bool:
        """检查一个组合是否已经被尝试过"""
        with self.lock:
            return combination in self._state["attempted_credentials"]

    def add_attempted(self, combination: Tuple[str, str]):
        """线程安全地添加一个已尝试的组合"""
        with self.lock:
            self._state["attempted_credentials"].add(combination)

    def cleanup_progress_file(self):
        """在任务成功完成后清理进度文件"""
        if self.progress_file and os.path.exists(self.progress_file):
            try:
                os.remove(self.progress_file)
                logging.info(f"任务成功，进度文件 '{self.progress_file}' 已被清理。")
            except OSError as e:
                logging.error(f"清理进度文件 '{self.progress_file}' 失败: {e}")
