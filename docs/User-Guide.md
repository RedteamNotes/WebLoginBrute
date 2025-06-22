# WebLoginBrute 用户指南

## 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/your-repo/WebLoginBrute.git
cd WebLoginBrute
pip install -e .

# 或使用 pip 安装
pip install webloginbrute
```

### 基本使用

```bash
# 最简单的用法
webloginbrute -u https://example.com/login -a https://example.com/auth -U users.txt -P passwords.txt

# 使用配置文件
webloginbrute --config config.yaml

# 详细输出模式
webloginbrute -u https://example.com/login -a https://example.com/auth -U users.txt -P passwords.txt --verbose
```

## 配置选项

### 命令行参数

| 参数 | 短参数 | 描述 | 示例 |
|------|--------|------|------|
| `--url` | `-u` | 登录表单页面URL | `https://example.com/login` |
| `--action` | `-a` | 登录表单提交URL | `https://example.com/auth` |
| `--users` | `-U` | 用户名字典文件 | `users.txt` |
| `--passwords` | `-P` | 密码字典文件 | `passwords.txt` |
| `--csrf` | `-s` | CSRF token字段名 | `csrf_token` |
| `--timeout` | `-T` | 请求超时时间（秒） | `30` |
| `--threads` | `-t` | 并发线程数 | `10` |
| `--aggressive` | `-A` | 对抗级别 | `2` |
| `--verbose` | | 详细输出 | |
| `--dry-run` | | 测试模式 | |

### 对抗级别

| 级别 | 描述 | 特点 |
|------|------|------|
| 0 | 静默模式 | 最小化网络活动，适合隐蔽测试 |
| 1 | 标准模式 | 平衡性能和隐蔽性 |
| 2 | 激进模式 | 高并发，快速测试 |
| 3 | 极限模式 | 最大并发，可能触发防护 |

### 安全级别

| 级别 | 描述 | 特点 |
|------|------|------|
| low | 低安全级别 | 最小安全检查，适合测试环境 |
| standard | 标准安全级别 | 平衡安全性和性能 |
| high | 高安全级别 | 严格安全检查，适合生产环境 |
| paranoid | 偏执安全级别 | 最高安全检查，可能影响性能 |

## 配置文件

### YAML 配置文件示例

```yaml
# config.yaml
url: "https://example.com/login"
action: "https://example.com/auth"
users: "wordlists/users.txt"
passwords: "wordlists/passwords.txt"

# 可选配置
csrf: "csrf_token"
login_field: "remember_me"
login_value: "1"
cookie: "cookies.txt"

# 性能配置
timeout: 30
threads: 10
aggressive: 2

# 内存管理
max_memory_mb: 1024
memory_warning_threshold: 80
memory_critical_threshold: 95

# 会话管理
session_rotation_interval: 300
session_lifetime: 1800
max_session_pool_size: 50

# 安全配置
security_level: "standard"
enable_health_check: true
validate_network_connectivity: true

# 日志配置
log: "progress.json"
verbose: true
```

### 环境变量配置

创建 `.env` 文件：

```bash
# 复制示例文件
cp env.example .env

# 编辑配置
nano .env
```

主要环境变量：

```bash
# 安全配置
WEBLOGINBRUTE_SECRET=your-super-secret-key-here
WEBLOGINBRUTE_ENCRYPTION_KEY=your-32-character-encryption-key

# 性能配置
WEBLOGINBRUTE_TIMEOUT=30
WEBLOGINBRUTE_THREADS=10
WEBLOGINBRUTE_MAX_MEMORY_MB=1024

# 安全级别
WEBLOGINBRUTE_SECURITY_LEVEL=standard
WEBLOGINBRUTE_ENABLE_HEALTH_CHECK=true
```

## 字典文件格式

### 用户名字典 (users.txt)

```
admin
administrator
root
user
test
guest
```

### 密码字典 (passwords.txt)

```
password
123456
admin
root
test
password123
```

### 自定义字典

```bash
# 生成常见用户名
echo -e "admin\nroot\nuser\ntest" > users.txt

# 生成常见密码
echo -e "password\n123456\nadmin\nroot" > passwords.txt

# 使用工具生成字典
crunch 4 4 0123456789 > numeric_passwords.txt
```

## 高级功能

### 会话管理

```bash
# 启用会话轮换
webloginbrute --session-rotation-interval 300 --session-lifetime 1800

# 禁用会话轮换
webloginbrute --disable-session-rotation

# 自定义轮换策略
webloginbrute --rotation-strategy request_count
```

### 内存管理

```bash
# 设置内存限制
webloginbrute --max-memory 2048 --memory-warning-threshold 80

# 自动内存清理
webloginbrute --memory-cleanup-interval 60
```

### 健康检查

```bash
# 启用健康检查
webloginbrute --enable-health-check

# 禁用网络验证
webloginbrute --disable-network-validation

# 禁用文件验证
webloginbrute --disable-file-validation
```

### 代理支持

```bash
# 使用HTTP代理
webloginbrute --proxy http://proxy:8080

# 使用SOCKS代理
webloginbrute --proxy socks5://proxy:1080

# 代理认证
webloginbrute --proxy-user username --proxy-pass password
```

## 输出和日志

### 进度文件

```json
{
  "start_time": "2024-01-01T12:00:00",
  "total_combinations": 1000,
  "current_position": 500,
  "successful_logins": [
    {
      "username": "admin",
      "password": "password",
      "timestamp": "2024-01-01T12:30:00"
    }
  ],
  "failed_attempts": 499,
  "errors": []
}
```

### 日志级别

```bash
# 详细日志
webloginbrute --verbose

# 调试日志
export WEBLOGINBRUTE_DEBUG=true
webloginbrute --config config.yaml
```

### 日志文件

- `webloginbrute.log`: 主日志文件
- `audit.log`: 审计日志
- `performance.log`: 性能日志
- `progress.json`: 进度文件

## 故障排除

### 常见问题

#### 1. 连接超时

```bash
# 增加超时时间
webloginbrute --timeout 60

# 检查网络连接
ping example.com
```

#### 2. 内存不足

```bash
# 减少内存使用
webloginbrute --max-memory 512 --threads 5

# 启用内存清理
webloginbrute --memory-cleanup-interval 30
```

#### 3. 被目标网站阻止

```bash
# 降低对抗级别
webloginbrute --aggressive 0

# 使用代理
webloginbrute --proxy http://proxy:8080

# 增加延迟
webloginbrute --delay 1
```

#### 4. CSRF Token 问题

```bash
# 指定CSRF字段
webloginbrute --csrf csrf_token

# 自动获取CSRF token
webloginbrute --auto-csrf
```

### 调试模式

```bash
# 启用调试模式
export WEBLOGINBRUTE_DEBUG=true
webloginbrute --config config.yaml

# 测试模式（不发送实际请求）
webloginbrute --dry-run --verbose
```

### 性能优化

#### 1. 提高并发

```bash
# 增加线程数
webloginbrute --threads 20

# 使用激进模式
webloginbrute --aggressive 3
```

#### 2. 优化字典

```bash
# 使用较小的字典
wc -l users.txt passwords.txt

# 排序和去重
sort -u users.txt > users_unique.txt
```

#### 3. 网络优化

```bash
# 使用本地代理
webloginbrute --proxy http://127.0.0.1:8080

# 调整超时
webloginbrute --timeout 15
```

## 安全最佳实践

### 1. 授权测试

- 仅在获得明确授权的目标上进行测试
- 遵守相关法律法规
- 记录所有测试活动

### 2. 配置安全

```bash
# 使用强密钥
export WEBLOGINBRUTE_SECRET="your-very-long-random-secret-key"

# 限制文件权限
chmod 600 .env
chmod 600 config.yaml
```

### 3. 日志安全

```bash
# 保护日志文件
chmod 600 *.log
chmod 600 *.json

# 定期清理敏感文件
rm -f *.log *.json
```

### 4. 网络安全

```bash
# 使用VPN或代理
webloginbrute --proxy socks5://vpn:1080

# 限制目标范围
webloginbrute --allowed-domains example.com
```

## 示例场景

### 场景1：基本登录测试

```bash
# 目标：测试常见用户名密码组合
webloginbrute \
  -u https://example.com/login \
  -a https://example.com/auth \
  -U common_users.txt \
  -P common_passwords.txt \
  -t 10 \
  --verbose
```

### 场景2：高安全性测试

```bash
# 目标：在安全环境中进行测试
webloginbrute \
  --config secure_config.yaml \
  --security-level high \
  --enable-health-check \
  --max-memory 2048 \
  --session-rotation-interval 180
```

### 场景3：隐蔽测试

```bash
# 目标：最小化被检测的风险
webloginbrute \
  -u https://example.com/login \
  -a https://example.com/auth \
  -U users.txt \
  -P passwords.txt \
  --aggressive 0 \
  --delay 2 \
  --proxy socks5://proxy:1080
```

### 场景4：大规模测试

```bash
# 目标：快速测试大量组合
webloginbrute \
  -u https://example.com/login \
  -a https://example.com/auth \
  -U large_users.txt \
  -P large_passwords.txt \
  --aggressive 3 \
  --threads 50 \
  --max-memory 4096
```

## 集成和自动化

### Python API 使用

```python
from webloginbrute import Config, WebLoginBrute

config = Config(
    url="https://example.com/login",
    action="https://example.com/auth",
    users="users.txt",
    passwords="passwords.txt",
    threads=10
)

brute = WebLoginBrute(config)
result = brute.run()

print(f"成功登录: {len(result['successful_logins'])}")
```

### 脚本自动化

```bash
#!/bin/bash
# 自动化测试脚本

# 设置环境变量
export WEBLOGINBRUTE_SECRET="your-secret-key"

# 运行测试
webloginbrute --config config.yaml --verbose

# 检查结果
if [ -f "progress.json" ]; then
    echo "测试完成，检查 progress.json 获取结果"
fi
```

### CI/CD 集成

```yaml
# .github/workflows/security-test.yml
name: Security Test
on: [push, pull_request]

jobs:
  security-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run WebLoginBrute
        run: |
          pip install webloginbrute
          webloginbrute --config test_config.yaml --dry-run
```

## 支持和社区

### 获取帮助

- 查看文档：`webloginbrute --help`
- 查看版本：`webloginbrute --version`
- 报告问题：GitHub Issues
- 讨论：GitHub Discussions

### 贡献

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

### 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。 