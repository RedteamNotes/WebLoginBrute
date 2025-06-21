# 配置说明

本文档详细介绍了WebLoginBrute的所有配置参数和选项。

## 📝 配置文件格式

WebLoginBrute使用YAML格式的配置文件，支持注释和分层结构。

```yaml
# 这是注释
parameter: value  # 行内注释
```

## 🔧 配置参数详解

### 目标配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `target_url` | string | ✅ | - | 登录页面URL |
| `success_redirect` | string | ✅ | - | 登录成功后的重定向URL |
| `failure_redirect` | string | ✅ | - | 登录失败后的重定向URL |

```yaml
# 目标配置示例
target_url: "https://example.com/login"
success_redirect: "https://example.com/dashboard"
failure_redirect: "https://example.com/login"
```

### 字典配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `username_list` | string | ✅ | - | 用户名列表文件路径 |
| `password_list` | string | ✅ | - | 密码列表文件路径 |

```yaml
# 字典配置示例
username_list: "usernames.txt"
password_list: "passwords.txt"
```

### 线程配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `threads` | integer | ✅ | 10 | 并发线程数 (1-100) |

```yaml
# 线程配置示例
threads: 10  # 推荐值：5-20
```

### 代理配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `proxy` | string | ❌ | null | 代理服务器地址 |

```yaml
# 代理配置示例
proxy: "http://127.0.0.1:8080"        # HTTP代理
proxy: "https://proxy.example.com:8080"  # HTTPS代理
proxy: "socks5://127.0.0.1:1080"      # SOCKS5代理
proxy: null                           # 不使用代理
```

### 对抗级别配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `aggression_level` | string | ❌ | "A1" | 对抗级别 (A0/A1/A2/A3) |

```yaml
# 对抗级别配置示例
aggression_level: "A0"  # 全速爆破
aggression_level: "A1"  # 低对抗
aggression_level: "A2"  # 中对抗
aggression_level: "A3"  # 高对抗
```

### 延迟配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `min_delay` | float | ❌ | 根据对抗级别 | 最小延迟时间(秒) |
| `max_delay` | float | ❌ | 根据对抗级别 | 最大延迟时间(秒) |
| `jitter_factor` | float | ❌ | 根据对抗级别 | 抖动因子(0-1) |

```yaml
# 延迟配置示例
min_delay: 1.0      # 最小延迟1秒
max_delay: 5.0      # 最大延迟5秒
jitter_factor: 0.3  # 30%抖动
```

### 智能延迟配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `enable_smart_delay` | boolean | ❌ | 根据对抗级别 | 启用智能延迟 |
| `enable_session_pool` | boolean | ❌ | 根据对抗级别 | 启用会话池管理 |
| `session_lifetime` | integer | ❌ | 根据对抗级别 | 会话生命周期(秒) |

```yaml
# 智能延迟配置示例
enable_smart_delay: true      # 启用智能延迟
enable_session_pool: true     # 启用会话池
session_lifetime: 300         # 会话5分钟过期
```

### 防护检测配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `enable_rate_limit_detection` | boolean | ❌ | 根据对抗级别 | 启用频率限制检测 |
| `enable_captcha_detection` | boolean | ❌ | 根据对抗级别 | 启用验证码检测 |

```yaml
# 防护检测配置示例
enable_rate_limit_detection: true   # 启用频率限制检测
enable_captcha_detection: true      # 启用验证码检测
```

### 进度保存配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `progress_file` | string | ❌ | "bruteforce_progress.json" | 进度保存文件 |

```yaml
# 进度保存配置示例
progress_file: "my_progress.json"  # 自定义进度文件
```

### 日志配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `log_level` | string | ❌ | "INFO" | 日志级别 |
| `log_file` | string | ❌ | "webloginbrute.log" | 日志文件路径 |

```yaml
# 日志配置示例
log_level: "DEBUG"           # 调试级别
log_file: "my_attack.log"    # 自定义日志文件
```

## 🎯 配置示例

### 基础配置

```yaml
# 基础爆破配置
target_url: "https://example.com/login"
success_redirect: "https://example.com/dashboard"
failure_redirect: "https://example.com/login"
username_list: "users.txt"
password_list: "passwords.txt"
threads: 10
aggression_level: "A1"
```

### 高安全目标配置

```yaml
# 高安全目标配置
target_url: "https://secure.example.com/login"
success_redirect: "https://secure.example.com/dashboard"
failure_redirect: "https://secure.example.com/login"
username_list: "users.txt"
password_list: "passwords.txt"
threads: 5
aggression_level: "A3"
proxy: "http://127.0.0.1:8080"
min_delay: 2.0
max_delay: 10.0
enable_session_pool: true
session_lifetime: 600
```

### 快速爆破配置

```yaml
# 快速爆破配置
target_url: "https://test.example.com/login"
success_redirect: "https://test.example.com/dashboard"
failure_redirect: "https://test.example.com/login"
username_list: "users.txt"
password_list: "passwords.txt"
threads: 20
aggression_level: "A0"
```

### 调试配置

```yaml
# 调试配置
target_url: "https://example.com/login"
success_redirect: "https://example.com/dashboard"
failure_redirect: "https://example.com/login"
username_list: "test_users.txt"
password_list: "test_passwords.txt"
threads: 1
aggression_level: "A1"
log_level: "DEBUG"
log_file: "debug.log"
```

## 🔄 配置继承和覆盖

### 对抗级别预设

每个对抗级别都有预设的配置值，您可以通过显式设置参数来覆盖：

```yaml
# A1级别默认配置
aggression_level: "A1"
# 默认值：
# min_delay: 0.5
# max_delay: 2.0
# enable_smart_delay: true
# enable_session_pool: false

# 覆盖默认值
aggression_level: "A1"
min_delay: 1.0      # 覆盖默认的0.5
max_delay: 3.0      # 覆盖默认的2.0
```

### 配置优先级

1. 用户显式设置的参数
2. 对抗级别预设值
3. 工具默认值

## 📁 配置文件管理

### 多配置文件

```bash
# 创建不同场景的配置文件
cp config.example.yaml config_prod.yaml
cp config.example.yaml config_test.yaml
cp config.example.yaml config_debug.yaml

# 使用不同配置
python3 webloginbrute.py --config config_prod.yaml
python3 webloginbrute.py --config config_test.yaml
```

### 配置验证

```bash
# 验证配置文件语法
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 验证配置参数
python3 webloginbrute.py --config config.yaml --validate
```

## 🛠️ 配置最佳实践

### 1. 安全配置

```yaml
# 生产环境安全配置
aggression_level: "A2"              # 使用中等对抗级别
threads: 5                          # 适中的线程数
enable_rate_limit_detection: true   # 启用防护检测
proxy: "http://proxy.example.com"   # 使用代理
log_level: "INFO"                   # 适当的日志级别
```

### 2. 性能配置

```yaml
# 高性能配置
aggression_level: "A0"              # 全速模式
threads: 20                         # 高并发
enable_smart_delay: false           # 关闭智能延迟
enable_session_pool: false          # 关闭会话池
```

### 3. 调试配置

```yaml
# 调试配置
threads: 1                          # 单线程便于调试
log_level: "DEBUG"                  # 详细日志
aggression_level: "A1"              # 基础对抗级别
enable_session_pool: false          # 简化会话管理
```

## ❓ 常见配置问题

### 1. 配置文件格式错误

```yaml
# 错误：缺少引号
target_url: https://example.com/login

# 正确：使用引号
target_url: "https://example.com/login"
```

### 2. 参数类型错误

```yaml
# 错误：字符串类型
threads: "10"

# 正确：整数类型
threads: 10
```

### 3. 路径问题

```yaml
# 错误：相对路径可能找不到文件
username_list: users.txt

# 正确：使用绝对路径或确保文件存在
username_list: "/path/to/users.txt"
username_list: "./users.txt"
```

---

**相关链接**: [快速开始](Getting-Started) | [对抗级别](Aggression-Levels) | [故障排除](Troubleshooting) 