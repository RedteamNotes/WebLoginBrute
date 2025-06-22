#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging

from .config.loaders import from_args_and_yaml
from .orchestrator import Orchestrator
from .utils.exceptions import ConfigurationError, BruteForceError
from .logger import setup_logging


def main():
    try:
        # 在加载配置之前设置一个临时的基本日志记录器
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        config = from_args_and_yaml()
        
        # 使用配置中的详细级别重新设置日志
        setup_logging(config.verbose)

        orchestrator = Orchestrator(config)
        orchestrator.run()

    except ConfigurationError as e:
        logging.error(f"配置错误: {e}", exc_info=True)
        sys.exit(2)
    except BruteForceError as e:
        logging.error(f"运行时错误: {e.to_dict()}", exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"程序执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
