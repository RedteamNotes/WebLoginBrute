#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebLoginBrute 版本管理模块
统一管理项目版本号，避免版本不一致问题
"""

__version__ = "0.27.9"
__author__ = "RedteamNotes"
__description__ = "Web登录暴力破解工具"

# 版本信息元组 (major, minor, patch)
VERSION_TUPLE = (0, 27, 2)

# 版本发布日期
RELEASE_DATE = "2024-12-19"

# 最低Python版本要求
MIN_PYTHON_VERSION = "3.8"


def get_version_info():
    """获取完整的版本信息"""
    return {
        "version": __version__,
        "version_tuple": VERSION_TUPLE,
        "author": __author__,
        "description": __description__,
        "release_date": RELEASE_DATE,
        "min_python_version": MIN_PYTHON_VERSION,
    }


def is_compatible_python_version():
    """检查当前Python版本是否兼容"""
    import sys

    current_version = sys.version_info[:2]
    required_version = tuple(map(int, MIN_PYTHON_VERSION.split(".")))
    return current_version >= required_version
