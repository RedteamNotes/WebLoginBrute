# 故障排除

本文档提供了WebLoginBrute使用过程中常见问题的解决方案。

## 📋 目录

- [安装问题](#安装问题)
- [配置问题](#配置问题)
- [运行问题](#运行问题)
- [性能问题](#性能问题)
- [网络问题](#网络问题)
- [日志分析](#日志分析)

## 🔧 安装问题

### 问题1：Python版本不兼容

#### 症状
```bash
SyntaxError: invalid syntax
# 或
ModuleNotFoundError: No module named 'requests'
```

#### 解决方案
```bash
# 检查Python版本
python3 --version

# 如果版本低于3.7，升级Python
# Ubuntu/Debian
sudo apt update
sudo apt install python3.9 python3.9-pip

# CentOS/RHEL
sudo yum install python39 python39-pip

# macOS
brew install python@3.9

# 使用虚拟环境
python3.9 -m venv webloginbrute_env
source webloginbrute_env/bin/activate
pip3 install -r requirements.txt
```

### 问题2：依赖安装失败

#### 症状
```bash
ERROR: Could not find a version that satisfies the requirement requests
ERROR: No matching distribution found for beautifulsoup4
```

#### 解决方案
```bash
# 升级pip
pip3 install --upgrade pip

# 使用国内镜像
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或使用conda
conda install requests beautifulsoup4 pyyaml lxml

# 手动安装核心依赖
pip3 install requests
pip3 install beautifulsoup4
pip3 install pyyaml
pip3 install lxml
```

### 问题3：权限问题

#### 症状
```bash
PermissionError: [Errno 13] Permission denied
```

#### 解决方案
```bash
# 使用用户安装
pip3 install --user -r requirements.txt

# 或使用sudo（不推荐）
sudo pip3 install -r requirements.txt

# 修复权限
sudo chown -R $USER:$USER ~/.local/lib/python3.*/site-packages/
```

## ⚙️ 配置问题

### 问题1：配置文件格式错误

#### 症状
```bash
yaml.parser.ParserError: while parsing a block mapping
```

#### 解决方案
```bash
# 检查YAML语法
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 常见错误修复
# 1. 缺少引号
target_url: https://example.com/login  # 错误
target_url: "https://example.com/login"  # 正确

# 2. 缩进错误
aggression_level: "A1"
  min_delay: 1.0  # 错误缩进
aggression_level: "A1"
min_delay: 1.0    # 正确缩进

# 3. 类型错误
threads: "10"     # 字符串类型
threads: 10       # 整数类型
```

### 问题2：文件路径错误

#### 症状
```bash
FileNotFoundError: [Errno 2] No such file or directory: 'users.txt'
```

#### 解决方案
```bash
# 检查文件是否存在
ls -la users.txt passwords.txt

# 使用绝对路径
username_list: "/full/path/to/users.txt"

# 或确保文件在当前目录
pwd
ls -la *.txt
```

### 问题3：URL格式错误

#### 症状
```bash
requests.exceptions.InvalidURL: Invalid URL
```

#### 解决方案
```yaml
# 错误格式
target_url: example.com/login
target_url: http://example.com/login  # 缺少协议

# 正确格式
target_url: "https://example.com/login"
target_url: "http://example.com/login"
```

## 🚀 运行问题

### 问题1：连接超时

#### 症状
```bash
requests.exceptions.ConnectTimeout: HTTPSConnectionPool
requests.exceptions.ReadTimeout: HTTPSConnectionPool
```

#### 解决方案
```yaml
# 增加超时时间
timeout: 30.0

# 使用代理
proxy: "http://127.0.0.1:8080"

# 减少线程数
threads: 5
```

### 问题2：SSL证书错误

#### 症状
```bash
requests.exceptions.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

#### 解决方案
```python
# 在代码中添加SSL验证禁用（不推荐用于生产环境）
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# 或使用代理绕过SSL
proxy: "http://127.0.0.1:8080"
```

### 问题3：CSRF Token获取失败

#### 症状
```bash
[ERROR] 无法获取CSRF Token
[ERROR] Token字段未找到
```

#### 解决方案
```bash
# 1. 手动分析页面
curl -s "https://target.com/login" | grep -i "csrf\|token"

# 2. 检查Token字段名
# 可能不是标准的"_token"，可能是：
# - "csrf_token"
# - "authenticity_token"
# - "_csrf_token"

# 3. 更新配置
csrf_field: "csrf_token"  # 使用正确的字段名
```

### 问题4：登录检测失败

#### 症状
```bash
[ERROR] 无法确定登录结果
[WARNING] 登录状态不明确
```

#### 解决方案
```yaml
# 1. 更新重定向URL
success_redirect: "https://target.com/dashboard"
failure_redirect: "https://target.com/login"

# 2. 使用自定义检测字符串
success_string: "Welcome"
failure_string: "Invalid credentials"

# 3. 检查响应状态码
# 成功通常返回200或302
# 失败通常返回200或401
```

## ⚡ 性能问题

### 问题1：速度过慢

#### 症状
```bash
平均速度: 1.2 次/秒
```

#### 解决方案
```yaml
# 1. 降低对抗级别
aggression_level: "A0"  # 全速模式

# 2. 增加线程数
threads: 20

# 3. 减少延迟
min_delay: 0.0
max_delay: 0.1

# 4. 关闭智能功能
enable_smart_delay: false
enable_session_pool: false
```

### 问题2：内存使用过高

#### 症状
```bash
MemoryError: Unable to allocate array
```

#### 解决方案
```yaml
# 1. 减少线程数
threads: 5

# 2. 关闭会话池
enable_session_pool: false

# 3. 分割大字典文件
split -l 1000 passwords.txt passwords_part_

# 4. 使用生成器处理大文件
```

### 问题3：CPU使用过高

#### 症状
```bash
# 系统变慢，风扇狂转
```

#### 解决方案
```bash
# 1. 限制CPU使用
# Linux
cpulimit -p $(pgrep python3) -l 50

# 2. 降低优先级
nice -n 10 python3 webloginbrute.py --config config.yaml

# 3. 减少线程数
threads: 3
```

## 🌐 网络问题

### 问题1：代理连接失败

#### 症状
```bash
requests.exceptions.ProxyError: HTTPConnectionPool
```

#### 解决方案
```bash
# 1. 测试代理连接
curl -x http://proxy:port https://httpbin.org/ip

# 2. 检查代理配置
proxy: "http://proxy.example.com:8080"

# 3. 使用认证代理
proxy: "http://user:pass@proxy.example.com:8080"

# 4. 尝试不同代理类型
proxy: "socks5://127.0.0.1:1080"
```

### 问题2：网络不稳定

#### 症状
```bash
requests.exceptions.ConnectionError: HTTPConnectionPool
```

#### 解决方案
```yaml
# 1. 增加重试次数
max_retries: 5

# 2. 增加超时时间
timeout: 30.0

# 3. 减少线程数
threads: 3

# 4. 使用更稳定的网络
```

### 问题3：DNS解析失败

#### 症状
```bash
requests.exceptions.ConnectionError: [Errno -2] Name or service not known
```

#### 解决方案
```bash
# 1. 检查DNS设置
nslookup target.com

# 2. 使用IP地址
target_url: "https://192.168.1.100/login"

# 3. 修改hosts文件
echo "192.168.1.100 target.com" >> /etc/hosts

# 4. 使用公共DNS
# 8.8.8.8 或 1.1.1.1
```

## 📊 日志分析

### 问题1：日志文件过大

#### 症状
```bash
# 日志文件占用大量磁盘空间
ls -lh webloginbrute.log
```

#### 解决方案
```bash
# 1. 压缩旧日志
gzip webloginbrute.log

# 2. 设置日志轮转
logrotate -f /etc/logrotate.d/webloginbrute

# 3. 调整日志级别
log_level: "WARNING"  # 减少日志输出
```

### 问题2：日志信息不清晰

#### 症状
```bash
# 日志信息混乱，难以分析
```

#### 解决方案
```bash
# 1. 使用结构化日志
log_format: "json"

# 2. 过滤关键信息
grep "SUCCESS" webloginbrute.log
grep "ERROR" webloginbrute.log
grep "rate limit" webloginbrute.log

# 3. 生成统计报告
python3 analyze_logs.py webloginbrute.log
```

### 问题3：调试信息不足

#### 症状
```bash
# 错误信息不够详细
```

#### 解决方案
```yaml
# 1. 启用调试模式
log_level: "DEBUG"

# 2. 启用详细输出
verbose: true

# 3. 保存响应内容
save_responses: true
```

## 🔍 诊断工具

### 1. 配置验证脚本

```python
#!/usr/bin/env python3
import yaml
import requests
import sys

def validate_config(config_file):
    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        # 验证必需参数
        required = ['target_url', 'username_list', 'password_list']
        for param in required:
            if param not in config:
                print(f"❌ 缺少必需参数: {param}")
                return False
        
        # 测试URL连接
        response = requests.get(config['target_url'], timeout=10)
        print(f"✅ URL连接正常: {response.status_code}")
        
        # 检查文件存在
        import os
        for file_param in ['username_list', 'password_list']:
            if os.path.exists(config[file_param]):
                print(f"✅ 文件存在: {config[file_param]}")
            else:
                print(f"❌ 文件不存在: {config[file_param]}")
                return False
        
        print("✅ 配置验证通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python3 validate_config.py config.yaml")
        sys.exit(1)
    
    success = validate_config(sys.argv[1])
    sys.exit(0 if success else 1)
```

### 2. 网络测试脚本

```bash
#!/bin/bash
# network_test.sh

TARGET_URL=$1
PROXY=$2

echo "测试目标连接..."
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n响应时间: %{time_total}s\n" "$TARGET_URL"

if [ ! -z "$PROXY" ]; then
    echo "测试代理连接..."
    curl -s -o /dev/null -w "代理HTTP状态码: %{http_code}\n代理响应时间: %{time_total}s\n" -x "$PROXY" "$TARGET_URL"
fi

echo "测试DNS解析..."
nslookup $(echo $TARGET_URL | sed 's|https://||' | sed 's|http://||' | cut -d'/' -f1)
```

### 3. 性能监控脚本

```bash
#!/bin/bash
# monitor_performance.sh

PID=$1
LOG_FILE=$2

echo "监控进程 $PID 的性能..."

while kill -0 $PID 2>/dev/null; do
    echo "=== $(date) ==="
    
    # CPU使用率
    CPU=$(ps -p $PID -o %cpu=)
    echo "CPU使用率: ${CPU}%"
    
    # 内存使用
    MEM=$(ps -p $PID -o %mem=)
    echo "内存使用: ${MEM}%"
    
    # 网络连接
    CONNS=$(netstat -an | grep ESTABLISHED | wc -l)
    echo "活跃连接: $CONNS"
    
    # 日志统计
    if [ ! -z "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
        SUCCESS=$(grep -c "SUCCESS" "$LOG_FILE")
        ERROR=$(grep -c "ERROR" "$LOG_FILE")
        echo "成功次数: $SUCCESS, 错误次数: $ERROR"
    fi
    
    sleep 10
done
```

## 📞 获取帮助

如果以上解决方案无法解决您的问题：

1. **查看日志文件**
```bash
tail -f webloginbrute.log
```

2. **启用调试模式**
```yaml
log_level: "DEBUG"
verbose: true
```

3. **收集系统信息**
```bash
python3 --version
pip3 list
uname -a
```

4. **提交问题报告**
- 在 [GitHub Issues](https://github.com/RedteamNotes/WebLoginBrute/issues) 提交问题
- 包含错误日志、配置文件和系统信息
- 描述复现步骤

---

**相关链接**: [快速开始](Getting-Started) | [配置说明](Configuration) | [使用教程](Tutorials) 