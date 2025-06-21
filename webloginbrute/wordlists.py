#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from .exceptions import ConfigurationError

def load_wordlist(path, config):
    """加载字典文件 - 生成器版本，避免内存压力"""
    # 验证文件路径
    if not os.path.exists(path):
        raise ConfigurationError(f"字典文件未找到: {path}")
    
    # 检查文件大小
    file_size = os.path.getsize(path)
    max_size = getattr(config, 'max_file_size', 100) * 1024 * 1024  # 可配置的MB限制
    if file_size > max_size:
        raise ConfigurationError(f"字典文件过大 ({file_size / 1024 / 1024:.1f}MB)，超过限制 {max_size / 1024 / 1024}MB")
    
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            max_lines = getattr(config, 'max_lines', 1000000)
            for i, line in enumerate(f):
                if i >= max_lines:
                    logging.warning(f"字典文件行数过多，只读取前{max_lines}行")
                    break
                stripped = line.strip()
                if stripped:
                    yield stripped
    except FileNotFoundError:
        raise ConfigurationError(f"字典文件未找到: {path}")
    except Exception as e:
        raise ConfigurationError(f"加载字典失败: {e}")

def load_wordlist_as_list(path, config):
    """加载字典文件为列表 - 用于小文件或需要列表的场景"""
    return list(load_wordlist(path, config))
