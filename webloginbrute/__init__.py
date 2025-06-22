from .version import __version__

# 检查Python版本兼容性
from .version import is_compatible_python_version
if not is_compatible_python_version():
    import sys
    print(f"错误: WebLoginBrute 需要 Python 3.8 或更高版本，当前版本: {sys.version}")
    sys.exit(1)

# 导出主要类和模块
from .config import Config
from .core import WebLoginBrute
from .exceptions import (
    BruteForceError, ConfigurationError, ValidationError,
    NetworkError, MemoryError, HealthCheckError, PerformanceError,
    SecurityError, RateLimitError
)
from .health_check import HealthChecker, run_health_checks, get_health_checker
from .logger import setup_logging, LogManager, get_log_manager
from .performance_monitor import PerformanceMonitor, get_performance_monitor
from .memory_manager import MemoryManager, get_memory_manager
from .http_client import HttpClient
from .state import StateManager
from .reporting import StatsManager
from .session_manager import SessionRotator, get_session_rotator
from .wordlists import load_wordlist

__all__ = [
    '__version__',
    'Config',
    'WebLoginBrute',
    'BruteForceError',
    'ConfigurationError',
    'ValidationError',
    'NetworkError',
    'MemoryError',
    'HealthCheckError',
    'PerformanceError',
    'SecurityError',
    'RateLimitError',
    'HealthChecker',
    'run_health_checks',
    'get_health_checker',
    'setup_logging',
    'LogManager',
    'get_log_manager',
    'PerformanceMonitor',
    'get_performance_monitor',
    'MemoryManager',
    'get_memory_manager',
    'HttpClient',
    'StateManager',
    'StatsManager',
    'SessionRotator',
    'get_session_rotator',
    'load_wordlist'
]
