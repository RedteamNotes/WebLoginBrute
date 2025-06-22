# 高级功能 (Advanced Features)

本文档介绍了 WebLoginBrute 的一些高级功能，旨在提升其在复杂场景下的灵活性和效率。

## 断点续扫 (Resume)

WebLoginBrute 支持断点续扫。如果在爆破过程中任务被中断（例如，手动停止或网络问题），你可以使用 `--resume` 或 `-r` 参数从上次保存的进度点继续，而无需从头开始。

### 工作原理
- 当任务启动时，程序会创建一个进度文件（默认为 `bruteforce_progress.json`）。
- 该文件记录了已尝试的所有用户名-密码组合。
- 使用 `--resume` 标志后，程序会首先读取该文件，跳过所有已记录的尝试。

### 使用方法

**启动一个可恢复的任务:**
```bash
webloginbrute \
  -u "https://target.com/login" \
  -U "users.txt" \
  -P "passwords.txt" \
  --log "my_task.json"
```

**中断后从进度文件恢复:**
```bash
webloginbrute \
  -u "https://target.com/login" \
  -U "users.txt" \
  -P "passwords.txt" \
  --log "my_task.json" \
  --resume
```
> **注意**: 为确保恢复成功，恢复时的核心参数（如 `url`, `users`, `passwords`）必须与初次运行时保持一致。

## 对抗级别 (Aggressive)

WebLoginBrute 提供4个对抗级别，用于在爆破速度和隐蔽性之间进行权衡，以应对不同的目标防护策略（如 WAF 或速率限制）。

### 级别说明

- **0 (静默模式)**: 无任何延迟，以最快速度发送请求。适合在没有速率限制的测试环境中快速验证。
- **1 (标准模式)**: **默认级别**。在请求之间引入微小、随机的延迟，模拟正常用户行为，尝试绕过简单的速率限制。
- **2 (激进模式)**: 引入更长、更随机的延迟，并可能伴随其他对抗策略。适合有中等强度防护的目标。
- **3 (极限模式)**: 采用最保守的策略，请求间隔最长，速度最慢。用于对抗高安全级别的目标，以避免被封禁。

### 使用示例

通过 `--aggressive` 或 `-A` 参数设置级别：

```bash
# 使用激进模式 (级别 2)
webloginbrute --config config.yaml --aggressive 2

# 在 YAML 文件中配置
# aggressive: 3
```

## 参数别名 (Alias)

为了方便习惯于其他工具的用户，WebLoginBrute 提供了一系列参数别名，以增强兼容性。

### 常用别名

| 标准参数 | 别名参数 |
|:---|:---|
| `-u`, `--url` | `--form-url` |
| `-a`, `--action` | `--submit-url` |
| `-U`, `--users` | `--username-file` |
| `-P`, `--passwords` | `--password-file` |
| `-s`, `--csrf` | `--csrf-field` |
| `-c`, `--cookie` | `--cookie-file` |
| `-l`, `--log` | `--progress-file` |
| `-A`, `--aggressive` | `--aggression-level` |

### 使用示例
以下两个命令是等效的：
```bash
webloginbrute -u "https://target.com/login" -U "users.txt"
```
```bash
webloginbrute --form-url "https://target.com/login" --username-file "users.txt"
```

## 环境变量配置

除了通过命令行和 YAML 文件，你还可以使用环境变量来配置 WebLoginBrute。这对于在 CI/CD 环境中或通过容器化部署时传递敏感信息（如密钥）特别有用。

### 工作原理
程序在启动时会自动读取以 `WEBLOGINBRUTE_` 开头的环境变量，并将其作为配置的一部分。

例如，你可以通过设置 `WEBLOGINBRUTE_THREADS` 环境变量来覆盖默认的线程数。

### 示例

**在 Linux/macOS 中:**
```bash
export WEBLOGINBRUTE_THREADS=15
export WEBLOGINBRUTE_TIMEOUT=60
webloginbrute --config config.yaml
```

**在 Windows (PowerShell) 中:**
```powershell
$env:WEBLOGINBRUTE_THREADS = "15"
$env:WEBLOGINBRUTE_TIMEOUT = "60"
webloginbrute --config config.yaml
```

环境变量的优先级低于命令行参数和 YAML 文件中的配置。

## 性能优化

### 内存优化

```