#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from typing import Optional, Dict, Any

from bs4 import BeautifulSoup, Tag


def contains_captcha(html: str) -> bool:
    """
    检测页面是否包含验证码。
    使用安全的html.parser，并优先进行简单的文本检查以提高性能。
    """
    if not html or not isinstance(html, str):
        return False

    # 优先使用快速的字符串检查
    html_lower = html.lower()
    if 'captcha' in html_lower or '验证码' in html_lower:
        return True

    # 如果需要更精确的检查，再解析HTML
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # 查找常见的验证码输入框或图像
        if soup.find('input', {'type': 'captcha'}) or soup.find('img', {'id': 'captcha_image'}):
            return True
    except Exception as e:
        logging.warning(f"解析HTML以检测验证码时失败: {e}")

    return False


def _find_in_dict(data: Dict[str, Any], key: str) -> Optional[Any]:
    """
    递归搜索字典中的键，支持点号路径 (e.g., 'data.token')。
    """
    # 如果key包含点号，按路径查找
    if '.' in key:
        keys = key.split('.')
        current = data
        try:
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return None
            return current
        except (KeyError, TypeError):
            return None
    else:
        # 否则，在字典中递归搜索
        if isinstance(data, dict):
            if key in data:
                return data[key]
            for value in data.values():
                if isinstance(value, dict):
                    found = _find_in_dict(value, key)
                    if found is not None:
                        return found
    return None


def extract_token(response_text: str, content_type: str, token_field: str) -> Optional[str]:
    """
    从响应中提取CSRF token。
    根据Content-Type智能选择JSON或HTML解析方式。
    """
    if not token_field or not response_text:
        return None

    # 处理JSON响应
    if "application/json" in content_type:
        try:
            # 限制JSON大小，防止内存攻击 (1MB)
            if len(response_text) > 1024 * 1024:
                logging.warning("JSON响应过大，跳过解析")
                return None
            json_data = json.loads(response_text)
            return _find_in_dict(json_data, token_field)
        except (json.JSONDecodeError, AttributeError):
            logging.warning(f"解析JSON以提取token '{token_field}' 时失败")
            return None

    # 处理HTML响应
    else:
        try:
            soup = BeautifulSoup(response_text, 'html.parser')
            token_input = soup.find('input', {'name': token_field})
            if isinstance(token_input, Tag) and token_input.has_attr('value'):
                value = token_input.get('value')
                # .get('value') 可能返回列表，我们只取第一个
                return value[0] if isinstance(value, list) else value
        except Exception as e:
            logging.warning(f"解析HTML以提取token '{token_field}' 时失败: {e}")
            return None
            
    return None


def analyze_form_fields(html: str) -> Optional[Dict[str, str]]:
    """
    分析登录表单，提取所有input字段及其默认值。
    """
    if not html or not isinstance(html, str):
        logging.warning("用于表单分析的HTML内容无效")
        return None

    try:
        soup = BeautifulSoup(html, 'html.parser')
        form = soup.find('form')
        if not isinstance(form, Tag):
            logging.warning("在页面中未检测到 <form> T元素")
            return None

        fields: Dict[str, str] = {}
        for inp in form.find_all('input'):
            if isinstance(inp, Tag) and inp.has_attr('name'):
                name_attr = inp.get('name')
                # 确保name是字符串
                name = name_attr[0] if isinstance(name_attr, list) else name_attr
                if not name:
                    continue
                
                value_attr = inp.get('value', '')
                # 确保value是字符串
                value = value_attr[0] if isinstance(value_attr, list) else value_attr
                fields[name] = value

        logging.info("表单字段自动探测结果：")
        for k, v in fields.items():
            logging.info(f"  - {k}: '{v}'")
        return fields
    except Exception as e:
        logging.warning(f"分析HTML表单字段时失败: {e}")
        return None
