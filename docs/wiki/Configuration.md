# 配置详解

本文档详细说明了 `WebLoginBrute` 的所有配置选项，您可以通过 **YAML 配置文件** 或 **命令行参数** 进行设置。

## 配置方式

### 1. YAML 配置文件 (推荐)
这是推荐的方式，尤其适用于复杂或需要复用的任务。

**示例 `config.yaml`:**
```yaml
# --- 核心配置 (必需) ---
url: "http://example.com/login"
action: "http://example.com/perform_login"
users: "wordlists/users.txt"
passwords: "wordlists/passwords.txt"

# --- 结果判断 (必需) ---
# 定义如何判断登录成功或失败，至少提供一个
success_string: "Welcome to your dashboard"
fail_string: "Invalid username or password"

# --- 性能与网络 ---
threads: 10
timeout: 20

# --- 功能选项 ---
csrf: "csrf_token"
resume: true
verbose: true
aggressive: "A2"
log: "my_task_progress.json"
```

**使用方法:**
```bash
python -m webloginbrute --config config.yaml
```

### 2. 命令行参数
您也可以直接通过命令行参数进行配置，这适用于简单的、一次性的任务。

**示例:**
```bash
python -m webloginbrute \
    --url "http://example.com/login" \
    --action "http://example.com/perform_login" \
    --users "wordlists/users.txt" \
    --passwords "wordlists/passwords.txt" \
    --fail-string "Invalid username or password" \
    --threads 10 \
    -v
```

### 配置优先级
**命令行参数 > YAML 文件 > 默认值**
- 如果一个选项同时在命令行和 YAML 文件中设置，将优先使用命令行中的值。

## 参数详解

### 核心参数 (Core)

| 参数名 | 命令行 | 类型 | 描述 |
| :--- | :--- | :--- | :--- |
| `url` | `-u`, `--url` | `string` | **必需。** 登录表单所在的页面 URL。 |
| `action` | `-a`, `--action` | `string` | **必需。** 表单提交的目标 URL。 |
| `users` | `-U`, `--users` | `string` | **必需。** 用户名字典文件的路径。 |
| `passwords` | `-P`, `--passwords` | `string` | **必需。** 密码字典文件的路径。 |

### 结果判断 (Result Identification)

| 参数名 | 命令行 | 类型 | 描述 |
| :--- | :--- | :--- | :--- |
| `success_string` | `--success-string` | `string` | 判断登录**成功**的特征字符串。 |
| `fail_string` | `--fail-string` | `string` | 判断登录**失败**的特征字符串。 |
| `success_redirect` | `--success-redirect` | `string` | 登录成功后会跳转到的目标 URL。 |
| `failure_redirect` | `--failure-redirect` | `string` | 登录失败后会跳转到的目标 URL。 |
> **注意**: 您必须至少提供以上四个选项中的一个，以便程序判断登录结果。

### 性能与网络 (Performance & Network)

| 参数名 | 命令行 | 类型 | 描述 |
| :--- | :--- | :--- | :--- |
| `threads` | `-t`, `--threads` | `int` | 并发线程数。默认为 `5`。 |
| `timeout` | `-T`, `--timeout` | `int` | HTTP 请求超时时间（秒）。默认为 `30`。 |
| `aggressive` | `-A`, `--aggressive` | `string` | 对抗级别 (`A0`, `A1`, `A2`, `A3`)。默认为 `A1`。 |

### 功能选项 (Features)

| 参数名 | 命令行 | 类型 | 描述 |
| :--- | :--- | :--- | :--- |
| `csrf` | `-s`, `--csrf` | `string` | CSRF Token 在表单中的 `name` 属性值。 |
| `cookie` | `-c`, `--cookie` | `string` | 包含预设 Cookie 的文件路径。 |
| `resume` | `-r`, `--resume` | `boolean` | 从上次中断处恢复爆破。默认为 `false`。 |
| `log` | `-g`, `--log` | `string` | 指定进度文件的保存路径。 |
| `dry_run` | `--dry-run` | `boolean` | 测试模式，不实际发送请求。|
| `verbose` | `-v`, `--verbose` | `boolean` | 启用详细日志输出。 |

## 参数概览

### 必需参数

| 参数 | 短参数 | 说明 | 示例 |
|------|--------|------|------|
| `--url` | `-u` | 登录表单页面URL | `-u https://target/login` |
| `--action` | `-a` | 登录表单提交URL | `-a https://target/login` |
| `--users` | `-U` | 用户名字典文件 | `-U users.txt` |
| `--passwords` | `-P` | 密码字典文件 | `-P passwords.txt` |

### 可选参数

| 参数 | 短参数 | 说明 | 默认值 | 示例 |
|------|--------|------|--------|------|
| `--config` | 无 | YAML配置文件 | 无 | `--config config.yaml` |
| `--csrf` | `-s` | CSRF token字段名 | 无 | `-s token` |
| `--login-field` | `-l` | 额外登录字段名 | 无 | `-l domain` |
| `--login-value` | `-w` | 额外登录字段值 | 无 | `-w example.com` |
| `--cookie` | `-c` | Cookie文件 | 无 | `-c cookies.txt` |
| `--timeout` | `-T` | 请求超时时间（秒） | 30 | `-T 60` |
| `--threads` | `-t` | 并发线程数 | 5 | `-t 10` |
| `--resume` | `-r` | 断点续扫 | False | `-r` |
| `--log` | `-g` | 进度文件路径 | bruteforce_progress.json | `-g state.json` |
| `--aggressive` | `-A` | 对抗级别 | A1 | `-A A2` |
| `--dry-run` | 无 | 测试模式 | False | `--dry-run` |
| `--verbose` | `-v` | 详细输出 | False | `-v` |
| `--version` | `-V` | 显示版本 | 无 | `-V` |
| `--help` | `-h` | 显示帮助 | 无 | `-h` |

## 详细说明

### 基础配置

#### `--url` / `-u`
登录表单页面的URL，用于获取CSRF token和表单字段信息。

```bash
-u https://target.com/login
```

#### `--action` / `-a`
登录表单提交的目标URL，实际的登录请求将发送到此地址。

```bash
-a https://target.com/login/authenticate
```

#### `--users` / `-U`
包含用户名的字典文件路径。支持txt格式，每行一个用户名。

```bash
-U wordlists/users.txt
```

#### `--passwords` / `-P`
包含密码的字典文件路径。支持txt格式，每行一个密码。

```bash
-P wordlists/passwords.txt
```

### 安全配置

#### `--csrf` / `-s`
目标网站的CSRF token字段名。如果目标没有CSRF保护，可以省略此参数。

```bash
-s csrf_token
```

#### `--cookie` / `-c`
Mozilla格式的Cookie文件路径，用于加载会话状态。

```bash
-c cookies.txt
```

### 性能配置

#### `--threads` / `-t`
并发线程数，影响爆破速度。建议根据目标性能和网络条件调整。

```bash
-t 10  # 使用10个并发线程
```

#### `--timeout` / `-T`
HTTP请求超时时间（秒）。网络较慢时可适当增加。

```bash
-T 60  # 60秒超时
```

#### `--aggressive` / `-A`
对抗级别，影响请求频率和隐蔽性：

- **A0 (静默模式)**: 最低对抗，适合测试环境
- **A1 (标准模式)**: 默认级别，平衡性能和隐蔽性
- **A2 (激进模式)**: 高对抗，适合有防护的目标
- **A3 (极限模式)**: 最高对抗，适合高安全性目标

```bash
-A A2  # 使用激进模式
```

### 进度管理

#### `--resume` / `-r`
启用断点续扫功能。程序会从上次中断的地方继续，避免重复工作。

```bash
-r  # 启用断点续扫
```

#### `--log` / `-g`
指定进度文件的保存路径。默认保存为 `bruteforce_progress.json`。

```bash
-g my_progress.json
```

### 输出控制

#### `--verbose` / `-v`
启用详细输出模式，显示DEBUG级别的日志信息。

```bash
-v  # 启用详细输出
```

#### `--dry-run` / `--dry-run`
测试模式，不实际发送登录请求，仅用于验证配置和流程。

```bash
--dry-run  # 测试模式
```

## YAML 配置文件

除了命令行参数，你还可以使用 YAML 配置文件来管理复杂的配置：

```yaml
# config.yaml
url: "https://target.com/login"
action: "https://target.com/login/authenticate"
users: "wordlists/users.txt"
passwords: "wordlists/passwords.txt"
csrf: "csrf_token"
threads: 10
aggressive: "A2"
verbose: true
resume: false
log: "my_progress.json"
```

使用配置文件：

```bash
python -m webloginbrute --config config.yaml
```

## 配置优先级

配置的优先级顺序（从高到低）：

1. **命令行参数** - 最高优先级
2. **YAML 配置文件** - 中等优先级
3. **默认值** - 最低优先级

这意味着命令行中指定的参数会覆盖配置文件中的相同设置。

## 最佳实践

### 1. 参数命名
- 使用短参数进行快速测试：`-u -a -U -P -t 10 -v`
- 使用长参数提高可读性：`--url --action --users --passwords --threads 10 --verbose`

### 2. 配置文件
- 对于复杂配置，使用 YAML 文件
- 为不同项目创建不同的配置文件
- 使用有意义的文件名：`project_a_config.yaml`

### 3. 性能调优
- 根据目标性能调整线程数
- 网络较慢时增加超时时间
- 有防护的目标使用更高的对抗级别

### 4. 安全考虑
- 定期清理进度文件
- 使用 `--dry-run` 测试配置
- 避免在日志中暴露敏感信息

## 故障排除

### 常见配置错误

1. **文件不存在**
   ```
   ValueError: 文件不存在: users.txt
   ```
   解决：检查文件路径是否正确

2. **URL格式错误**
   ```
   ValueError: URL必须以http://或https://开头
   ```
   解决：确保URL包含协议前缀

3. **参数冲突**
   ```
   error: argument -v/--verbose: conflicting option string: -v
   ```
   解决：检查是否有重复的参数定义

### 配置验证

使用 `--dry-run` 模式验证配置：

```bash
python -m webloginbrute -u https://target/login -a https://target/login -U users.txt -P passwords.txt --dry-run
```

这将检查所有配置项而不实际发送请求。

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
url: "http://example.com/login"
action: "http://example.com/perform_login"
users: "wordlists/users.txt"
passwords: "wordlists/passwords.txt"

# --- 可选配置 ---
csrf: "csrf_token_name"
threads: 15
timeout: 20
resume: true
verbose: true
aggressive: "A2"
```

### 3. 运行

使用 `--config-file` 参数来指定你的配置文件：

```bash
python -m webloginbrute --config my_task.yaml
```

---

## 方式二：命令行参数

对于快速、一次性的任务，直接使用命令行参数非常方便。

### 基础用法

```bash
python -m webloginbrute \
    --url "http://example.com/login" \
    --action "http://example.com/perform_login" \
    --users "wordlists/users.txt" \
    --passwords "wordlists/passwords.txt"
```

### 高级用法

你可以组合使用多个参数来实现更复杂的功能：

```bash
python -m webloginbrute \
    --url "http://example.com/login" \
    --action "http://example.com/perform_login" \
    --users "wordlists/users.txt" \
    --passwords "wordlists/passwords.txt" \
    --csrf "csrf_token" \
    --threads 10 \
    --resume \
    --verbose
```

---

## 所有配置项详解

下表列出了所有可用的配置项，它们既可以用于YAML文件（作为键），也可以用于命令行（作为参数）。

| YAML 键 (`key`) | 命令行参数 (`--key`) | 类型 | 描述 |
| :--- | :--- | :--- | :--- |
| **`url`** | `--url` | `string` | **必需**. 包含登录表单的页面URL。 |
| **`action`** | `--action` | `string` | **必需**. 登录表单提交的目标URL。 |
| **`users`** | `--users` | `string` | **必需**. 用户名字典文件的路径。 |
| **`passwords`** | `--passwords` | `string` | **必需**. 密码字典文件的路径。 |
| `csrf` | `--csrf` | `string` | 目标网站使用的CSRF Token字段的`name`属性。 |
| `login_field` | `--login-field` | `string` | 额外的登录字段名。 |
| `login_value` | `--login-value` | `string` | 额外的登录字段值。 |
| `threads` | `--threads` | `integer` | 并发线程数。默认为 `5`。 |
| `timeout` | `--timeout` | `integer` | HTTP请求的超时时间（秒）。默认为 `30`。 |
| `cookie` | `--cookie` | `string` | Mozilla `cookies.txt` 格式的Cookie文件路径。 |
| `resume` | `--resume` | `boolean` | 设置为 `true` 或在命令行使用此标志，以从上次中断处恢复。 |
| `log` | `--log` | `string` | 指定进度文件的路径。默认为 `bruteforce_progress.json`。 |
| `dry_run` | `--dry-run` | `boolean` | 测试模式。设置为 `true` 或在命令行使用此标志，将不会实际发送攻击请求。 |
| `aggressive` | `--aggressive` | `string` | 对抗级别 (`A0`, `A1`, `A2`, `A3`)。默认为 `A1`。 |
| `verbose` | `--verbose` | `boolean` | 详细模式。设置为 `true` 或在命令行使用此标志，将在控制台输出DEBUG日志。 |
| `ip_whitelist` | *N/A* | `array` | (仅YAML) IP白名单，支持CIDR。 |
| `