#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import chardet
from functools import lru_cache
from typing import Iterator
from .memory_manager import get_memory_manager

from .exceptions import ConfigurationError, MemoryError


@lru_cache(maxsize=32)
def detect_encoding(file_path: str) -> str:
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(1024 * 1024)  # 读取1MB用于检测
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result['confidence'] > 0.7 else 'utf-8'
            if encoding is None:
                encoding = 'utf-8'
            logging.debug(f"检测到文件编码: {encoding} (置信度: {result['confidence']:.2f})")
            return encoding
    except Exception as e:
        logging.warning(f"编码检测失败，使用默认UTF-8: {e}")
        return 'utf-8'


def load_wordlist(path: str, config=None, chunk_size: int = 10000) -> Iterator[str]:
    """
    分块读取字典文件，防止内存溢出

    Args:
        path: 字典文件路径
        config: 配置对象
        chunk_size: 分块大小

    Yields:
        str: 字典项

    Raises:
        ConfigurationError: 文件不存在或格式错误
        MemoryError: 内存不足
    """
    # 验证文件路径
    if not os.path.exists(path):
        raise ConfigurationError(f"字典文件未找到: {path}")

    # 检查文件大小
    file_size = os.path.getsize(path)
    max_size = getattr(config, "max_file_size", 100) * 1024 * 1024  # 可配置的MB限制
    if file_size > max_size:
        raise ConfigurationError(
            f"字典文件过大 ({file_size / 1024 / 1024:.1f}MB)，超过限制 {max_size / 1024 / 1024}MB"
        )

    # 获取内存管理器
    memory_manager = get_memory_manager()

    # 估算文件行数和内存需求
    estimated_lines = file_size // 20  # 假设平均每行20字节
    estimated_memory_mb = estimated_lines * 0.001  # 假设每行占用1KB

    # 检查内存限制
    if not memory_manager.check_memory_limit(estimated_memory_mb):
        raise MemoryError(f"预估内存需求 {estimated_memory_mb:.1f}MB 超过限制")

    # 检测文件编码
    encoding = detect_encoding(path)

    try:
        with open(path, 'rb') as f:
            raw_data = f.read(4096)
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'

        with open(path, 'r', encoding=encoding, errors='ignore') as f:
            chunk = []
            line_count = 0
            max_lines = getattr(config, "max_lines", 1000000)

            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    chunk.append(line)
                    line_count += 1

                    # 检查行数限制
                    if line_count >= max_lines:
                        logging.warning(f"字典文件行数过多，只读取前{max_lines}行")
                        break

                    # 检查chunk大小
                    if len(chunk) >= chunk_size:
                        # 检查内存使用
                        with memory_manager.memory_context():
                            for item in chunk:
                                yield item
                        chunk = []

                        # 定期检查内存
                        if line_count % (chunk_size * 10) == 0:
                            memory_stats = memory_manager.get_memory_stats()
                            logging.debug(
                                f"已处理 {line_count} 行，当前内存: {memory_stats['current_memory']:.1f}MB")

            # 处理剩余的chunk
            if chunk:
                with memory_manager.memory_context():
                    for item in chunk:
                        yield item

    except UnicodeDecodeError as e:
        logging.error(f"文件编码错误: {e}")
        # 尝试使用其他编码
        fallback_encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        for fallback_encoding in fallback_encodings:
            try:
                with open(path, "r", encoding=fallback_encoding, errors="replace") as f:
                    max_lines = getattr(config, "max_lines", 1000000)
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            logging.warning(f"字典文件行数过多，只读取前{max_lines}行")
                            break
                        stripped = line.strip()
                        if stripped and not stripped.startswith('#'):
                            # 检查内存使用
                            with memory_manager.memory_context():
                                yield stripped
                logging.info(f"使用备用编码 {fallback_encoding} 成功读取文件")
                return
            except UnicodeDecodeError:
                continue
        raise ConfigurationError(f"无法使用任何编码读取文件: {path}")
    except FileNotFoundError:
        raise ConfigurationError(f"字典文件未找到: {path}")
    except Exception as e:
        raise ConfigurationError(f"加载字典失败: {e}")


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
        raise MemoryError(f"文件过大，预估内存需求 {estimated_memory_mb:.1f}MB 超过限制")

    with memory_manager.memory_context(estimated_memory_mb):
        return list(load_wordlist(path, config))


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
        with open(file_path, 'rb') as f:
            sample_data = f.read(sample_size)
            line_count = sample_data.count(b'\n')

        # 估算总行数
        estimated_lines = int(line_count * file_size / sample_size)
        estimated_memory_mb = estimated_lines * 0.001  # 假设每行1KB

        return {
            'file_size_mb': file_size / 1024 / 1024,
            'estimated_lines': estimated_lines,
            'estimated_memory_mb': estimated_memory_mb,
            'sample_size_mb': sample_size / 1024 / 1024
        }
    except Exception as e:
        logging.warning(f"估算文件大小失败: {e}")
        return {
            'file_size_mb': file_size / 1024 / 1024,
            'estimated_lines': None,
            'estimated_memory_mb': None,
            'sample_size_mb': sample_size / 1024 / 1024
        }
