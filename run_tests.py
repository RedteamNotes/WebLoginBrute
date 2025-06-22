#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试运行脚本
运行所有单元测试并生成覆盖率报告
"""

import os
import sys
import subprocess
import unittest
from pathlib import Path

def run_tests():
    """运行所有测试"""
    print("🧪 开始运行测试...")
    
    # 添加项目根目录到Python路径
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # 发现并运行所有测试
    loader = unittest.TestLoader()
    start_dir = str(project_root / 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()

def run_coverage():
    """运行覆盖率测试"""
    print("📊 开始运行覆盖率测试...")
    
    try:
        # 检查是否安装了coverage
        import coverage
    except ImportError:
        print("❌ coverage未安装，跳过覆盖率测试")
        print("💡 安装命令: pip install coverage")
        return False
    
    # 运行覆盖率测试
    cmd = [
        sys.executable, '-m', 'coverage', 'run', 
        '--source=webloginbrute', 
        '-m', 'unittest', 'discover', 'tests'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        # 生成覆盖率报告
        report_cmd = [sys.executable, '-m', 'coverage', 'report']
        report_result = subprocess.run(report_cmd, capture_output=True, text=True)
        
        if report_result.returncode == 0:
            print("📈 覆盖率报告:")
            print(report_result.stdout)
            
            # 生成HTML报告
            html_cmd = [sys.executable, '-m', 'coverage', 'html']
            subprocess.run(html_cmd, capture_output=True)
            print("📁 HTML报告已生成到 htmlcov/ 目录")
            
            return True
        else:
            print("❌ 生成覆盖率报告失败")
            print(report_result.stderr)
            return False
    else:
        print("❌ 覆盖率测试失败")
        print(result.stderr)
        return False

def run_linting():
    """运行代码检查"""
    print("🔍 开始代码检查...")
    
    try:
        import flake8
    except ImportError:
        print("❌ flake8未安装，跳过代码检查")
        print("💡 安装命令: pip install flake8")
        return False
    
    # 运行flake8检查
    cmd = [sys.executable, '-m', 'flake8', 'webloginbrute', 'tests']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 代码检查通过")
        return True
    else:
        print("❌ 代码检查发现问题:")
        print(result.stdout)
        return False

def run_security_check():
    """运行安全检查"""
    print("🔒 开始安全检查...")
    
    try:
        import bandit
    except ImportError:
        print("❌ bandit未安装，跳过安全检查")
        print("💡 安装命令: pip install bandit")
        return False
    
    # 运行bandit安全检查
    cmd = [
        sys.executable, '-m', 'bandit', 
        '-r', 'webloginbrute',
        '-f', 'txt'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 安全检查通过")
        return True
    else:
        print("⚠️  安全检查发现问题:")
        print(result.stdout)
        return False

def main():
    """主函数"""
    print("🚀 WebLoginBrute 测试套件")
    print("=" * 50)
    
    # 运行各种测试
    tests_passed = run_tests()
    coverage_passed = run_coverage()
    linting_passed = run_linting()
    security_passed = run_security_check()
    
    # 总结结果
    print("\n" + "=" * 50)
    print("📋 测试结果总结:")
    print(f"  单元测试: {'✅ 通过' if tests_passed else '❌ 失败'}")
    print(f"  覆盖率测试: {'✅ 通过' if coverage_passed else '❌ 失败'}")
    print(f"  代码检查: {'✅ 通过' if linting_passed else '❌ 失败'}")
    print(f"  安全检查: {'✅ 通过' if security_passed else '❌ 失败'}")
    
    # 返回总体结果
    overall_success = tests_passed and coverage_passed and linting_passed and security_passed
    print(f"\n总体结果: {'✅ 全部通过' if overall_success else '❌ 存在问题'}")
    
    return 0 if overall_success else 1

if __name__ == '__main__':
    sys.exit(main()) 