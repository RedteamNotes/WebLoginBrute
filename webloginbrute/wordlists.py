#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import chardet

from .exceptions import ConfigurationError


def detect_encoding(file_path: str) -> str:
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(1024 * 1024)  # 读取1MB用于检测
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result['confidence'] > 0.7 else 'utf-8'
            logging.debug(f"检测到文件编码: {encoding} (置信度: {result['confidence']:.2f})")
            return encoding
    except Exception as e:
        logging.warning(f"编码检测失败，使用默认UTF-8: {e}")
        return 'utf-8'


def load_wordlist(path, config):
    """加载字典文件 - 生成器版本，避免内存压力"""
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

    # 检测文件编码
    encoding = detect_encoding(path)
    
    try:
        with open(path, "r", encoding=encoding, errors="replace") as f:
            max_lines = getattr(config, "max_lines", 1000000)
            for i, line in enumerate(f):
                if i >= max_lines:
                    logging.warning(f"字典文件行数过多，只读取前{max_lines}行")
                    break
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):  # 忽略注释行
                    yield stripped
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


def load_wordlist_as_list(path, config):
    """加载字典文件为列表 - 用于小文件或需要列表的场景"""
    return list(load_wordlist(path, config))
