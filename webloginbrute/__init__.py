#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebLoginBrute: A fast and modular web login bruteforcer.
"""

__all__ = [
    "__version__",
    "is_compatible_python_version",
    "Orchestrator",
    "Config",
    "from_args_and_yaml",
    "BruteForceError",
    "ConfigurationError",
    "NetworkError",
    "SecurityError",
]

from .version import __version__, is_compatible_python_version
from .config.models import Config
from .config.loaders import from_args_and_yaml
from .orchestrator import Orchestrator
from .utils.exceptions import (
    BruteForceError,
    ConfigurationError,
    NetworkError,
    SecurityError,
)

# 运行时检查
if not is_compatible_python_version():
    import sys
    sys.exit("Python 3.8 or higher is required.")
