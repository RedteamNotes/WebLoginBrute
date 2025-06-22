#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import chardet
from functools import lru_cache
from typing import List, Generator
from ..services.memory_manager import get_memory_manager

from .exceptions import ConfigurationError, MemoryError


@lru_cache(maxsize=32)
def detect_encoding(file_path: str) -> str:
    """检测文件编码"""
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read(1024 * 1024)  # 读取1MB用于检测
            result = chardet.detect(raw_data)
            encoding = result["encoding"] if result["confidence"] > 0.7 else "utf-8"
            if encoding is None:
                encoding = "utf-8"
            logging.debug(
                f"检测到文件编码: {encoding} (置信度: {result['confidence']:.2f})"
            )
            return encoding
    except Exception as e:
        logging.warning(f"编码检测失败，使用默认UTF-8: {e}")
        return "utf-8"


def load_wordlist(
    file_path: str, encoding: str = "utf-8", max_size: int = 100 * 1024 * 1024
) -> List[str]:
    """
    从文件加载字典，支持多种编码和大型文件。

    :param file_path: 字典文件路径
    :param encoding: 文件编码
    :param max_size: 最大文件大小（字节）
    :return: 包含字典内容的列表
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"字典文件不存在: {file_path}")

    if os.path.getsize(file_path) > max_size:
        raise ValueError(f"文件大小超过限制 ({max_size} bytes)")

    wordlist = []
    try:
        with open(file_path, "r", encoding=encoding) as f:
            for line in f:
                wordlist.append(line.strip())
    except UnicodeDecodeError:
        # 尝试其他常用编码
        common_encodings = ["latin-1", "gbk", "utf-16"]
        for enc in common_encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    wordlist = [line.strip() for line in f]
                return wordlist
            except UnicodeDecodeError:
                continue
        raise
    except Exception as e:
        raise IOError(f"读取字典文件失败: {e}") from e

    return wordlist


def load_wordlist_as_list(path: str, config) -> list:
    """
    加载字典文件为列表 - 用于小文件或需要列表的场景

    Args:
        path: 字典文件路径
        config: 配置对象

    Returns:
        list: 字典项列表

    Raises:
        ConfigurationError: 文件不存在或格式错误
        MemoryError: 内存不足
    """
    memory_manager = get_memory_manager()

    # 检查文件大小
    file_size = os.path.getsize(path)
    estimated_memory_mb = file_size / 1024 / 1024 * 2  # 预估内存需求

    if not memory_manager.check_memory_limit(estimated_memory_mb):
        raise MemoryError(
            f"文件过大，预估内存需求 {estimated_memory_mb:.1f}MB 超过限制"
        )

    with memory_manager.memory_context(estimated_memory_mb):
        return list(load_wordlist(path))


def estimate_wordlist_size(file_path: str) -> dict:
    """
    估算字典文件的大小和内存需求

    Args:
        file_path: 字典文件路径

    Returns:
        dict: 包含文件大小、行数、预估内存等信息
    """
    if not os.path.exists(file_path):
        raise ConfigurationError(f"文件不存在: {file_path}")

    file_size = os.path.getsize(file_path)

    # 采样估算行数
    sample_size = min(file_size, 1024 * 1024)  # 1MB采样
    line_count = 0

    try:
        with open(file_path, "rb") as f:
            sample_data = f.read(sample_size)
            line_count = sample_data.count(b"\n")

        # 估算总行数
        estimated_lines = int(line_count * file_size / sample_size)
        estimated_memory_mb = estimated_lines * 0.001  # 假设每行1KB

        return {
            "file_size_mb": file_size / 1024 / 1024,
            "estimated_lines": estimated_lines,
            "estimated_memory_mb": estimated_memory_mb,
            "sample_size_mb": sample_size / 1024 / 1024,
        }
    except Exception as e:
        logging.warning(f"估算文件大小失败: {e}")
        return {
            "file_size_mb": file_size / 1024 / 1024,
            "estimated_lines": None,
            "estimated_memory_mb": None,
            "sample_size_mb": sample_size / 1024 / 1024,
        }
