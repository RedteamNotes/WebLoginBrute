from .version import __version__

# 检查Python版本兼容性
from .version import is_compatible_python_version
if not is_compatible_python_version():
    import sys
    print(f"错误: WebLoginBrute 需要 Python 3.8 或更高版本，当前版本: {sys.version}")
    sys.exit(1)
