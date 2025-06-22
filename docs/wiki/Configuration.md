# 配置指南

**版本：0.0.27**

WebLoginBrute 提供了两种灵活的配置方式，以适应不同的使用场景：**命令行参数**和**YAML配置文件**。

> **优先级规则**: 如果同时使用命令行参数和配置文件，**命令行参数将覆盖配置文件中的同名设置**。

---

## 方式一：YAML 配置文件 (推荐)

对于复杂或需要重复执行的任务，我们强烈推荐使用YAML配置文件。这种方式清晰、易于管理和版本控制。

### 1. 创建配置文件

你可以从项目根目录下的 [`config.example.yaml`](../../config.example.yaml) 文件开始。将它复制为你自己的配置文件，例如 `my_task.yaml`。

### 2. 编辑配置

打开你的 `.yaml` 文件并根据需求修改参数。一个典型的配置文件如下：

```yaml
# my_task.yaml

# --- 核心配置 (必需) ---
form_url: "http://example.com/login"
submit_url: "http://example.com/perform_login"
username_file: "wordlists/users.txt"
password_file: "wordlists/passwords.txt"

# --- 可选配置 ---
csrf: "csrf_token_name"
threads: 15
timeout: 20
resume: true
verbose: true
aggression_level: "A2"
```

### 3. 运行

使用 `--config-file` 参数来指定你的配置文件：

```bash
python -m webloginbrute --config-file my_task.yaml
```

---

## 方式二：命令行参数

对于快速、一次性的任务，直接使用命令行参数非常方便。

### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--form` | 登录表单URL | `--form https://example.com/login` |
| `--submit` | 登录提交URL | `--submit https://example.com/login` |
| `--users` | 用户名字典文件 | `--users wordlists/users.txt` |
| `--passwords` | 密码字典文件 | `--passwords wordlists/passwords.txt` |

### 可选参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--config` | YAML配置文件路径 | - | `--config config.yaml` |
| `--csrf` | CSRF token字段名 | - | `--csrf csrf_token` |
| `--field` | 额外的登录字段名 | - | `--field remember` |
| `--value` | 额外的登录字段值 | - | `--value 1` |
| `--cookies` | Cookie文件路径 | - | `--cookies cookies.txt` |
| `--timeout` | 请求超时时间（秒） | 30 | `--timeout 15` |
| `--threads` | 并发线程数 | 5 | `--threads 10` |
| `--resume` | 从上次中断的地方继续 | false | `--resume` |
| `--progress` | 进度文件路径 | `bruteforce_progress.json` | `--progress my_progress.json` |
| `--level` | 对抗级别 | A1 | `--level A2` |
| `--dry-run` | 测试模式，不实际发送请求 | false | `--dry-run` |
| `--verbose` | 详细输出 | false | `--verbose` |

### 高级用法

```bash
# 带CSRF token的登录
python -m webloginbrute \
    --form "https://example.com/login" \
    --submit "https://example.com/login" \
    --users "wordlists/users.txt" \
    --passwords "wordlists/passwords.txt" \
    --csrf "csrf_token"

# 使用Cookie文件
python -m webloginbrute \
    --form "https://example.com/login" \
    --submit "https://example.com/login" \
    --users "users.txt" \
    --passwords "passwords.txt" \
    --cookies "cookies.txt"

# 高并发配置
python -m webloginbrute \
    --form "https://example.com/login" \
    --submit "https://example.com/login" \
    --users "users.txt" \
    --passwords "passwords.txt" \
    --threads 20 \
    --timeout 10

# 从上次中断的地方继续
python -m webloginbrute \
    --form "https://example.com/login" \
    --submit "https://example.com/login" \
    --users "users.txt" \
    --passwords "passwords.txt" \
    --resume \
    --progress "my_progress.json"
```

---

## 所有配置项详解

下表列出了所有可用的配置项，它们既可以用于YAML文件（作为键），也可以用于命令行（作为参数）。

| YAML 键 (`key`) | 命令行参数 (`--key`) | 类型 | 描述 |
| :--- | :--- | :--- | :--- |
| **`form_url`** | `--form-url` | `string` | **必需**. 包含登录表单的页面URL。 |
| **`submit_url`** | `--submit-url` | `string` | **必需**. 登录表单提交的目标URL。 |
| **`username_file`** | `--username-file` | `string` | **必需**. 用户名字典文件的路径。 |
| **`password_file`** | `--password-file` | `string` | **必需**. 密码字典文件的路径。 |
| `csrf` | `--csrf` | `string` | 目标网站使用的CSRF Token字段的`name`属性。 |
| `login_field` | `--login-field` | `string` | 额外的登录字段名。 |
| `login_value` | `--login-value` | `string` | 额外的登录字段值。 |
| `threads` | `--threads` | `integer` | 并发线程数。默认为 `5`。 |
| `timeout` | `--timeout` | `integer` | HTTP请求的超时时间（秒）。默认为 `30`。 |
| `cookie_file` | `--cookie-file` | `string` | Mozilla `cookies.txt` 格式的Cookie文件路径。 |
| `resume` | `--resume` | `boolean` | 设置为 `true` 或在命令行使用此标志，以从上次中断处恢复。 |
| `progress_file` | `--progress-file` | `string` | 指定进度文件的路径。默认为 `bruteforce_progress.json`。 |
| `dry_run` | `--dry-run` | `boolean` | 测试模式。设置为 `true` 或在命令行使用此标志，将不会实际发送攻击请求。 |
| `aggression_level` | `--aggression-level` | `string` | 对抗级别 (`A0`, `A1`, `A2`, `A3`)。默认为 `A1`。 |
| `verbose` | `--verbose` | `boolean` | 详细模式。设置为 `true` 或在命令行使用此标志，将在控制台输出DEBUG日志。 |
| `ip_whitelist` | *N/A* | `array` | (仅YAML) IP白名单，支持CIDR。 |
| `ip_blacklist` | *N/A* | `array` | (仅YAML) IP黑名单，支持CIDR。 | 