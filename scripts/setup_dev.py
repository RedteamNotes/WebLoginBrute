#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开发环境设置脚本
安装所有开发依赖并配置开发环境
"""

import os
import sys
import subprocess
import venv
from pathlib import Path


def run_command(cmd, description):
    """运行命令并处理结果"""
    print(f"🔄 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ {description} 完成")
        return True
    else:
        print(f"❌ {description} 失败")
        print(f"错误信息: {result.stderr}")
        return False


def create_virtual_env():
    """创建虚拟环境"""
    venv_path = Path("venv")
    if venv_path.exists():
        print("📁 虚拟环境已存在")
        return True

    print("📁 创建虚拟环境...")
    try:
        venv.create("venv", with_pip=True)
        print("✅ 虚拟环境创建完成")
        return True
    except Exception as e:
        print(f"❌ 虚拟环境创建失败: {e}")
        return False


def install_dependencies():
    """安装依赖"""
    # 确定pip路径
    if os.name == "nt":  # Windows
        pip_path = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_path = "venv/bin/pip"

    # 升级pip
    run_command(f"{pip_path} install --upgrade pip", "升级pip")

    # 安装核心依赖
    run_command(f"{pip_path} install -r requirements.txt", "安装核心依赖")

    # 安装开发依赖
    dev_deps = [
        "coverage>=7.0.0",
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "flake8>=6.0.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "bandit>=1.7.0",
        "safety>=2.0.0",
        "mypy>=1.0.0",
        "types-PyYAML>=6.0.0",
        "types-requests>=2.31.0",
    ]

    for dep in dev_deps:
        run_command(f"{pip_path} install {dep}", f"安装 {dep}")


def setup_git_hooks():
    """设置Git钩子"""
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        print("📁 .git目录不存在，跳过Git钩子设置")
        return

    # 创建pre-commit钩子
    pre_commit_content = """#!/bin/sh
# Pre-commit钩子 - 运行代码检查

echo "🔍 运行代码检查..."

# 运行flake8
python -m flake8 webloginbrute tests
if [ $? -ne 0 ]; then
    echo "❌ 代码检查失败，请修复问题后重试"
    exit 1
fi

# 运行black检查
python -m black --check webloginbrute tests
if [ $? -ne 0 ]; then
    echo "❌ 代码格式检查失败，请运行 'black webloginbrute tests' 修复格式"
    exit 1
fi

# 运行isort检查
python -m isort --check-only webloginbrute tests
if [ $? -ne 0 ]; then
    echo "❌ 导入排序检查失败，请运行 'isort webloginbrute tests' 修复排序"
    exit 1
fi

echo "✅ 代码检查通过"
"""

    pre_commit_path = hooks_dir / "pre-commit"
    with open(pre_commit_path, "w") as f:
        f.write(pre_commit_content)

    # 设置执行权限
    os.chmod(pre_commit_path, 0o755)
    print("✅ Git钩子设置完成")


def create_config_files():
    """创建配置文件"""
    # 创建.flake8配置文件
    flake8_config = """[flake8]
max-line-length = 120
exclude = .git,__pycache__,venv,build,dist
ignore = E203, W503
"""

    with open(".flake8", "w") as f:
        f.write(flake8_config)

    # 创建pyproject.toml的black配置
    black_config = """[tool.black]
line-length = 120
target-version = ['py38']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
)/
'''
"""

    with open("pyproject.toml", "a") as f:
        f.write("\n" + black_config)

    print("✅ 配置文件创建完成")


def run_initial_tests():
    """运行初始测试"""
    print("🧪 运行初始测试...")

    # 确定python路径
    if os.name == "nt":  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_path = "venv/bin/python"

    # 运行测试
    success = run_command(f"{python_path} run_tests.py", "运行测试套件")

    if success:
        print("✅ 初始测试通过")
    else:
        print("⚠️  初始测试存在问题，请检查并修复")


def main():
    """主函数"""
    print("🚀 WebLoginBrute 开发环境设置")
    print("=" * 50)

    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return 1

    print(f"✅ Python版本: {sys.version}")

    # 创建虚拟环境
    if not create_virtual_env():
        return 1

    # 安装依赖
    install_dependencies()

    # 设置Git钩子
    setup_git_hooks()

    # 创建配置文件
    create_config_files()

    # 运行初始测试
    run_initial_tests()

    print("\n" + "=" * 50)
    print("🎉 开发环境设置完成！")
    print("\n📋 下一步:")
    print("1. 激活虚拟环境:")
    if os.name == "nt":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. 运行测试: python run_tests.py")
    print("3. 格式化代码: black webloginbrute tests")
    print("4. 排序导入: isort webloginbrute tests")
    print("5. 代码检查: flake8 webloginbrute tests")

    return 0


if __name__ == "__main__":
    sys.exit(main())
