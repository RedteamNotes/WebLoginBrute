# WebLoginBrute 用户手册

本文档提供了 WebLoginBrute 的详细使用说明，帮助您快速上手并有效利用其各项功能。

## 目录
- [简介](#简介)
- [安装](#安装)
- [快速开始](#快速开始)
- [配置](#配置)
  - [配置文件 (`config.yaml`)](#配置文件-configyaml)
  - [命令行参数](#命令行参数)
- [核心功能](#核心功能)
  - [性能配置](#性能配置)
  - [内存管理](#内存管理)
  - [会话管理](#会话管理)
  - [健康检查](#健康检查)
  - [安全策略](#安全策略)
- [使用示例](#使用示例)
  - [基础爆破](#基础爆破)
  - [使用 Cookie 和 CSRF Token](#使用-cookie-和-csrf-token)
  - [调整性能参数](#调整性能参数)
  - [从中断处恢复](#从中断处恢复)

---

## 简介
WebLoginBrute 是一款功能强大的模块化 Web 登录页面爆破工具。它支持高度自定义的配置，集成了性能监控、内存管理、会话管理、健康检查和安全策略等高级功能，旨在提供高效、稳定和安全的测试体验。

## 安装
通过 pip 从 git 仓库直接安装:
```bash
pip install git+https://github.com/RedteamNotes/WebLoginBrute.git
```
或者克隆仓库后手动安装:
```bash
git clone https://github.com/RedteamNotes/WebLoginBrute.git
cd WebLoginBrute
pip install .
```

## 快速开始
1. **创建配置文件 `config.yaml`**:
   ```yaml
   url: "http://test.com/login.php"
   action: "http://test.com/login.php"
   users: "/path/to/users.txt"
   passwords: "/path/to/passwords.txt"
   csrf: "user_token" # 登录表单中 CSRF token 的字段名
   threads: 10
   timeout: 20
   ```

2. **准备字典文件**:
   - `users.txt`: 每行一个用户名。
   - `passwords.txt`: 每行一个密码。

3. **运行工具**:
   ```bash
   webloginbrute --config config.yaml
   ```

## 配置
WebLoginBrute 支持通过 YAML 配置文件和命令行参数进行配置。命令行参数会覆盖配置文件中的同名设置。

### 配置文件 (`config.yaml`)
这是推荐的配置方式，可以将所有选项集中管理。

**示例 `config.yaml`**:
```yaml
# 基础配置 (必需)
url: "http://target.com/login"          # 登录页面 URL
action: "http://target.com/dologin"      # 表单提交 URL
users: "wordlists/users.txt"             # 用户名字典
passwords: "wordlists/passwords.txt"     # 密码字典

# 可选配置
csrf: "_csrf_token"                      # CSRF Token 字段名
login_field: "extra_param"               # 额外的登录字段名
login_value: "extra_value"               # 额外的登录字段值
cookie: "/path/to/cookies.txt"           # Cookie 文件路径

# 性能配置
threads: 10                              # 并发线程数 (默认: 5)
timeout: 15                              # 请求超时 (秒) (默认: 30)
aggressive: 1                            # 对抗级别 (0-3) (默认: 1)

# 内存管理
max_memory_mb: 2048                      # 最大内存使用 (MB) (默认: 1024)

# 会话管理
enable_session_rotation: true            # 启用会话轮换 (默认: true)

# 健康检查
enable_health_check: true                # 启用健康检查 (默认: true)

# 安全配置
security_level: "standard"               # 安全级别 (默认: "standard")
allowed_domains: ["target.com"]          # 允许的域名

# 操作配置
resume: false                            # 从上次中断处继续 (默认: false)
log: "brute_progress.log"                # 进度日志文件
dry_run: false                           # 测试模式，不发请求 (默认: false)
verbose: true                            # 详细输出 (默认: false)
```

### 命令行参数
您可以通过命令行参数快速调整配置。

| 参数                  | 缩写 | 描述                                       | 默认值          |
|-----------------------|------|--------------------------------------------|-----------------|
| `--config`            | -c   | YAML 配置文件路径                          | `None`          |
| `--url`               | -u   | 登录页面 URL                               | (必需)          |
| `--action`            | -a   | 表单提交 URL                               | (必需)          |
| `--users`             |      | 用户名字典路径                             | (必需)          |
| `--passwords`         | -p   | 密码字典路径                               | (必需)          |
| `--csrf`              |      | CSRF Token 字段名                          | `None`          |
| `--login_field`       |      | 额外的登录字段名                           | `None`          |
| `--login_value`       |      | 额外的登录字段值                           | `None`          |
| `--cookie`            |      | Cookie 文件路径                            | `None`          |
| `--threads`           | -t   | 并发线程数                                 | `5`             |
| `--timeout`           |      | 请求超时时间（秒）                         | `30`            |
| `--aggressive`        |      | 对抗级别 (0-3)                             | `1`             |
| `--resume`            |      | 从上次中断的地方继续                       | `False`         |
| `--log`               | -l   | 进度文件路径                               | `None`          |
| `--dry_run`           |      | 测试模式，不实际发送请求                   | `False`         |
| `--verbose`           | -v   | 详细输出                                   | `False`         |

---

## 核心功能
### 性能配置
- **`threads`**: 控制并发请求数量，提高爆破速度。
- **`timeout`**: 设置网络请求的超时时间，避免因网络问题导致长时间等待。
- **`aggressive`**: 设置对抗级别，调整请求频率和模式以应对不同的目标防护策略。
  - `0`: 静默模式，最低请求频率。
  - `1`: 标准模式，常规请求。
  - `2`: 激进模式，提高请求频率。
  - `3`: 极限模式，最大化请求速度。

### 内存管理
通过 `max_memory_mb` 和其他相关参数，工具能够监控自身内存使用情况，在达到阈值时自动进行清理，防止因字典过大或长时间运行导致内存溢出。

### 会话管理
当 `enable_session_rotation` 启用时，工具会定期更换会话（如 User-Agent、代理等），模拟多用户行为，以绕过基于会话的访问限制。

### 健康检查
在启动时，工具会执行一系列健康检查（`enable_health_check`），包括：
- **网络连通性**: 检查目标 URL 是否可达。
- **文件完整性**: 验证字典文件是否存在、可读，且大小在限制范围内。
- **安全策略**: 确保目标域名在允许列表中。

### 安全策略
- **`security_level`**: 预设的安全配置级别 (`standard`, `strict`, `paranoid`)。
- **`allowed_domains`**: 限制工具只对指定的域名发起请求，防止误操作。
- **`blocked_domains`**: 禁止向指定的域名发起请求。

---

## 使用示例

### 基础爆破
```bash
webloginbrute --url "http://example.com/login" \
              --action "http://example.com/login" \
              --users users.txt \
              --passwords passwords.txt \
              -t 20 \
              -v
```

### 使用 Cookie 和 CSRF Token
适用于需要登录状态或有 CSRF 防护的页面。

**`config.yaml`**:
```yaml
url: "https://secure.site/login"
action: "https://secure.site/auth"
users: "users.txt"
passwords: "passwords.txt"
cookie: "my_cookies.txt"
csrf: "csrf_token"
threads: 5
```

**运行**:
```bash
webloginbrute -c config.yaml -v
```

### 调整性能参数
在高带宽、低延迟网络下，可以尝试更激进的配置。
```bash
webloginbrute -c config.yaml --threads 50 --aggressive 2
```

### 从中断处恢复
如果爆破意外中断，可以使用 `--resume` 标志从上次保存的进度继续。
```bash
webloginbrute -c config.yaml --resume -l progress.log
```
这要求之前运行时已通过 `-l` 或 `log` 配置项指定了进度文件。 