# 故障排除

本文档提供了在使用 WebLoginBrute 过程中常见问题的诊断和解决方案。

## 📋 目录

- [安装与环境问题](#安装与环境问题)
- [配置问题](#配置问题)
- [运行问题](#运行问题)
- [性能问题](#性能问题)
- [网络问题](#网络问题)
- [日志分析](#日志分析)

## 🔧 安装与环境问题

### 问题：`ModuleNotFoundError: No module named 'some_dependency'`
**症状**: 启动时报告找不到某个模块，如 `pydantic`, `requests` 等。
**原因**:
1.  依赖未正确安装。
2.  您没有在安装了依赖的 Python 虚拟环境中运行程序。

**解决方案**:
1.  **激活虚拟环境**: 确保您已经激活了为本项目创建的虚拟环境。
```bash
    # macOS/Linux
    source venv/bin/activate
    # Windows
    .\venv\Scripts\Activate.ps1
    ```
2.  **重新安装依赖**: 在项目根目录下，再次运行安装命令。
```bash
    pip install .
```

### 问题：`webloginbrute: command not found`
**症状**: 在终端输入 `webloginbrute` 后，系统提示命令未找到。
**原因**:
1.  项目未正确安装。
2.  虚拟环境未激活，导致命令不在系统的 `PATH` 中。

**解决方案**:
1.  确认您已成功执行 `pip install .`。
2.  **必须激活虚拟环境**，因为这是将 `webloginbrute` 命令添加到 `PATH` 的标准方式。

## ⚙️ 配置问题

### 问题：启动时出现 `ConfigurationError: ...`
**症状**: 程序启动失败，并抛出一个 `ConfigurationError`。
**原因**: 这是最常见的错误，由 Pydantic 配置模型触发，意味着你的配置（来自 YAML 或命令行）不符合要求。
**解决方案**:
-   **仔细阅读错误信息**: `ConfigurationError` 通常会明确指出是哪个字段出了问题以及原因。
-   **检查文件路径**: 如果错误信息中包含 "文件不存在"，请使用 `ls` 或 `dir` 命令确认你的字典文件（`users`, `passwords`）或 `cookie` 文件路径是否相对于你**当前运行命令的目录**是正确的。
-   **检查 URL 格式**: 确保 `url` 和 `action` 字段的值以 `http://` 或 `https://` 开头。
-   **检查 YAML 语法**: 确保 `config.yaml` 文件中的缩进是正确的（通常是2个空格），并且值（如布尔值 `true`/`false`，数字）没有被错误地用引号括起来。

## 🚀 运行问题

### 问题：所有登录尝试都立即失败，或出现大量连接错误
**症状**: 日志中快速滚动大量失败信息，或出现 `ConnectionTimeout`, `ConnectionError` 等网络相关的异常。
**原因**:
1.  **IP 被封禁或速率限制**: 目标网站的 WAF 或安全策略已检测到异常活动并开始阻止你的请求。
2.  **网络问题**: 你的本地网络到目标服务器不稳定。
3.  **SSL/TLS 问题**: 目标网站使用了不受信任的 SSL 证书（常见于测试环境）。

**解决方案**:
1.  **增加对抗性**: 这是首要步骤。降低请求速率以避免被检测。
    -   提高对抗级别: `--aggressive 2` 或 `3`。
    -   减少并发线程数: `--threads 5` 或更低。
2.  **增加超时时间**: 如果网络慢，可以尝试增加超时时间 `--timeout 60`。
3.  **检查目标可访问性**: 尝试用浏览器或 `curl` 直接访问目标 URL，看是否正常。
4.  **处理 SSL 验证 (不推荐)**: 如果你完全信任目标，并且确定是证书问题，可以在代码层面暂时禁用 SSL 验证（**这会带来安全风险**）。但更好的方法是让目标服务器管理员修复证书。

### 问题：程序能运行，但一个正确的密码也找不到
**症状**: 程序正常运行，所有尝试都显示失败，但你确信字典中有正确的用户名和密码。
**原因**: 这几乎总是因为发送给服务器的登录请求不完整或不正确。
**解决方案**:
1.  **检查 CSRF Token**: 这是最常见的原因。使用浏览器开发者工具找到正确的 CSRF token 字段名，并通过 `--csrf <token_name>` 提供。
2.  **检查额外的表单数据**: 登录表单可能包含其他必需的隐藏字段。例如，一个名为 `login_type` 值为 `standard` 的字段。你需要通过 `--login-field login_type --login-value standard` 来添加它们。可以多次使用这两个参数来添加多个字段。
3.  **检查 `action` URL**: 默认情况下，表单会提交到 `--url`。如果登录请求需要提交到不同的地址，请务必使用 `--action <submit_url>` 明确指定。
4.  **使用 Cookie**: 某些登录流程需要预设的会话 Cookie。你可以将 Cookie 保存到文件，并用 `--cookie <cookie_file>` 加载。
5.  **开启详细输出**: 使用 `--verbose` 模式运行，它可能会打印出更多有助于诊断的调试信息。

## ⚡ 性能问题

### 问题：程序运行速度远低于预期
**症状**: 即使在低对抗级别下，每秒请求数（RPS）也很低。
**原因**:
1.  **目标服务器响应慢**: 这是最主要的原因。如果目标服务器处理每个请求都需要2-3秒，那么无论你设置多高的线程数，总速率都会很低。
2.  **网络延迟高**: 你的网络到目标服务器的 RTT (Round-Trip Time) 过高。
3.  **线程数设置不当**: 线程数并非越多越好。过高的线程数可能导致本地资源（CPU/内存）瓶颈或触发目标更严格的速率限制。

**解决方案**:
1.  **诊断瓶颈**: 使用 `ping <target_domain>` 或 `traceroute <target_domain>` 来评估网络延迟。
2.  **合理设置线程数**: 从较低的线程数开始（如 `-t 10`），然后逐步增加，观察速率变化。找到一个增长不再明显的拐点，就是最佳线程数。
3.  **接受现实**: 如果瓶颈在于目标服务器，那么除了更换测试目标，你无能为力。

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
url: "https://192.168.1.100/login"

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
        required = ['url', 'users', 'passwords']
        for param in required:
            if param not in config:
                print(f"❌ 缺少必需参数: {param}")
                return False
        
        # 测试URL连接
        response = requests.get(config['url'], timeout=10)
        print(f"✅ URL连接正常: {response.status_code}")
        
        # 检查文件存在
        import os
        for file_param in ['users', 'passwords']:
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

URL=$1
PROXY=$2

echo "测试目标连接..."
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n响应时间: %{time_total}s\n" "$URL"

if [ ! -z "$PROXY" ]; then
    echo "测试代理连接..."
    curl -s -o /dev/null -w "代理HTTP状态码: %{http_code}\n代理响应时间: %{time_total}s\n" -x "$PROXY" "$URL"
fi

echo "测试DNS解析..."
nslookup $(echo $URL | sed 's|https://||' | sed 's|http://||' | cut -d'/' -f1)
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