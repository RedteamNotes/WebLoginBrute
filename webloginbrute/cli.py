#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from .config import Config
from .core import WebLoginBrute
from .exceptions import ConfigurationError


def main():
    try:
        config = Config()
        brute = WebLoginBrute(config)
        brute.run()
    except ConfigurationError as e:
        print(f"[配置错误] {e}")
        sys.exit(2)
    except KeyboardInterrupt:
        print("\n[!] 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"[!] 程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
