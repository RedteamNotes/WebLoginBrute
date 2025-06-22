# 高级功能

**版本：0.0.27**

本文档介绍WebLoginBrute提供的一些高级功能，帮助你更好地应对复杂的测试场景。

## 智能进度恢复

当你处理一个包含数百万组合的大型字典时，爆破任务可能会因为各种原因（如网络中断、目标重启）而意外终止。WebLoginBrute的进度恢复功能可以让你从上次中断的地方无缝继续，而不会丢失任何进度。

### 如何使用

-   **通过命令行**: 添加 `--resume` 标志。
    ```bash
    python -m webloginbrute --config-file my_task.yaml --resume
    ```
-   **通过YAML文件**: 设置 `resume: true`。
    ```yaml
    # my_task.yaml
    # ... 其他配置 ...
    resume: true
    ```

### 工作原理

-   当任务进行时，程序会定期将已尝试的用户名和密码组合记录到一个进度文件（默认为 `bruteforce_progress.json`）中。
-   使用 `--resume` 标志启动时，程序会首先加载这个文件，并将所有已记录的组合添加到一个跳过列表中。
-   这样，新的任务会直接跳过所有已经尝试过的组合，从中断处继续。
-   任务成功结束后，进度文件会被自动删除。

你可以使用 `--progress-file` 参数指定自定义的进度文件路径。

## 对抗级别

WebLoginBrute提供了4个对抗级别，用于适应不同的安全环境：

### A0 - 静默模式
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --level A0
```

### A1 - 标准模式（默认）
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --level A1
```

### A2 - 激进模式
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --level A2
```

### A3 - 极限模式
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --level A3
```

## 进度恢复

### 启用进度恢复
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --resume \
  --progress my_progress.json
```

### 自定义进度文件
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --resume \
  --progress /path/to/custom_progress.json
```

## 高级配置

### 使用Cookie文件
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --cookies cookies.txt
```

### 额外登录字段
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --field remember \
  --value 1
```

### 高并发配置
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --threads 20 \
  --timeout 10
```

### 测试模式
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --dry-run \
  --verbose
```

## 详细日志 (`--verbose`)

当你需要排查问题或深入了解程序的每一个步骤时，可以启用详细日志模式。

### 如何使用

-   **通过命令行**: 添加 `--verbose` 标志。
-   **通过YAML文件**: 设置 `verbose: true`。

启用后，控制台会输出 `DEBUG` 级别的日志，显示包括HTTP请求头、响应状态码、提取的Token等在内的详细信息。同时，`logs/` 目录下的日志文件也会记录这些信息。 