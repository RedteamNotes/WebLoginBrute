# API 参考 - 配置 (`Config`)

本文档详细介绍了 `WebLoginBrute` 的核心配置类 `Config`。所有配置项均可通过 YAML 文件或命令行参数进行设置，并支持环境变量。

## `Config` 类
核心配置类，使用 Pydantic 进行数据验证。

---

### 基础配置 (必需)

**`url: str`**
- **描述**: 目标登录页面的 URL。工具会访问此页面以获取表单和 CSRF Token（如果需要）。
- **YAML**: `url`
- **CLI**: `--url` / `-u`
- **验证**: 必须是有效的 HTTP/HTTPS URL。

**`action: str`**
- **描述**: 登录表单提交的目标 URL。
- **YAML**: `action`
- **CLI**: `--action` / `-a`
- **验证**: 必须是有效的 HTTP/HTTPS URL。

**`users: str`**
- **描述**: 用户名字典文件的路径。
- **YAML**: `users`
- **CLI**: `--users`
- **验证**: 文件必须存在且可读。

**`passwords: str`**
- **描述**: 密码字典文件的路径。
- **YAML**: `passwords`
- **CLI**: `--passwords` / `-p`
- **验证**: 文件必须存在且可读。

---

### 可选登录配置

**`csrf: Optional[str]`**
- **描述**: 登录表单中 CSRF Token 隐藏字段的 `name` 属性。
- **YAML**: `csrf`
- **CLI**: `--csrf`
- **默认值**: `None`

**`login_field: Optional[str]`**
- **描述**: 除用户名和密码外，需要提交的额外字段的 `name` 属性。
- **YAML**: `login_field`
- **CLI**: `--login_field`
- **默认值**: `None`

**`login_value: Optional[str]`**
- **描述**: `login_field` 对应的值。
- **YAML**: `login_value`
- **CLI**: `--login_value`
- **默认值**: `None`

**`cookie: Optional[str]`**
- **描述**: 包含认证 Cookie 的文件路径。
- **YAML**: `cookie`
- **CLI**: `--cookie`
- **验证**: 如果提供，文件必须存在。
- **默认值**: `None`

---

### 性能配置

**`timeout: int`**
- **描述**: 网络请求的超时时间（秒）。
- **YAML**: `timeout`
- **CLI**: `--timeout`
- **环境变量**: `WEBLOGINBRUTE_TIMEOUT`
- **约束**: `1` <= `timeout` <= `300`
- **默认值**: `30`

**`threads: int`**
- **描述**: 并发执行的线程数量。
- **YAML**: `threads`
- **CLI**: `--threads` / `-t`
- **环境变量**: `WEBLOGINBRUTE_THREADS`
- **约束**: `1` <= `threads` <= `100`
- **默认值**: `5`

**`aggressive: int`**
- **描述**: 对抗级别，影响请求延迟和模式。
  - `0`: 静默 (最低频率)
  - `1`: 标准
  - `2`: 激进
  - `3`: 极限 (最高频率)
- **YAML**: `aggressive`
- **CLI**: `--aggressive`
- **环境变量**: `WEBLOGINBRUTE_AGGRESSIVE_LEVEL`
- **约束**: `0` <= `aggressive` <= `3`
- **默认值**: `1`

---

### 内存管理配置

**`max_memory_mb: int`**
- **描述**: 允许应用使用的最大内存量 (MB)。
- **YAML**: `max_memory_mb`
- **环境变量**: `WEBLOGINBRUTE_MAX_MEMORY_MB`
- **约束**: `128` <= `max_memory_mb` <= `8192`
- **默认值**: `1024`

**`memory_warning_threshold: int`**
- **描述**: 内存使用达到此百分比时触发警告。
- **YAML**: `memory_warning_threshold`
- **环境变量**: `WEBLOGINBRUTE_MEMORY_WARNING_THRESHOLD`
- **约束**: `50` <= `threshold` <= `95`
- **默认值**: `80`

**`memory_critical_threshold: int`**
- **描述**: 内存使用达到此百分比时触发严重警告并可能暂停任务。
- **YAML**: `memory_critical_threshold`
- **环境变量**: `WEBLOGINBRUTE_MEMORY_CRITICAL_THRESHOLD`
- **约束**: `80` <= `threshold` <= `99`
- **默认值**: `95`

**`memory_cleanup_interval: int`**
- **描述**: 内存清理任务的运行间隔（秒）。
- **YAML**: `memory_cleanup_interval`
- **环境变量**: `WEBLOGINBRUTE_MEMORY_CLEANUP_INTERVAL`
- **约束**: `10` <= `interval` <= `300`
- **默认值**: `60`

---

### 会话管理配置

**`enable_session_rotation: bool`**
- **描述**: 是否启用会话轮换（如更换 User-Agent）。
- **YAML**: `enable_session_rotation`
- **环境变量**: `WEBLOGINBRUTE_ENABLE_SESSION_ROTATION`
- **默认值**: `True`

**`session_rotation_interval: int`**
- **描述**: 会话轮换的时间间隔（秒）。
- **YAML**: `session_rotation_interval`
- **环境变量**: `WEBLOGINBRUTE_SESSION_ROTATION_INTERVAL`
- **约束**: `60` <= `interval` <= `3600`
- **默认值**: `300`

---

### 健康检查配置

**`enable_health_check: bool`**
- **描述**: 是否在启动时执行健康检查。
- **YAML**: `enable_health_check`
- **环境变量**: `WEBLOGINBRUTE_ENABLE_HEALTH_CHECK`
- **默认值**: `True`

**`validate_network_connectivity: bool`**
- **描述**: 是否检查与目标 URL 的网络连通性。
- **YAML**: `validate_network_connectivity`
- **环境变量**: `WEBLOGINBRUTE_ENABLE_NETWORK_VALIDATION`
- **默认值**: `True`

**`validate_file_integrity: bool`**
- **描述**: 是否检查字典等文件的存在性和可读性。
- **YAML**: `validate_file_integrity`
- **环境变量**: `WEBLOGINBRUTE_ENABLE_FILE_VALIDATION`
- **默认值**: `True`

**`max_file_size: int`**
- **描述**: 字典等文件的最大允许大小 (MB)。
- **YAML**: `max_file_size`
- **环境变量**: `WEBLOGINBRUTE_MAX_FILE_SIZE`
- **约束**: `1` <= `size` <= `1000`
- **默认值**: `100`

---

### 安全配置

**`security_level: str`**
- **描述**: 安全策略级别 (`standard`, `strict`, `paranoid`)。
- **YAML**: `security_level`
- **环境变量**: `WEBLOGINBRUTE_SECURITY_LEVEL`
- **默认值**: `standard`

**`allowed_domains: List[str]`**
- **描述**: 允许发起请求的域名列表。如果列表不为空，`url` 和 `action` 的域名必须在此列表内。
- **YAML**: `allowed_domains`
- **默认值**: `[]` (空列表)

**`blocked_domains: List[str]`**
- **描述**: 禁止发起请求的域名列表。
- **YAML**: `blocked_domains`
- **默认值**: `[]` (空列表)

---

### 操作配置

**`resume: bool`**
- **描述**: 是否从上次中断的进度恢复任务。需要配合 `log` 参数使用。
- **YAML**: `resume`
- **CLI**: `--resume`
- **默认值**: `False`

**`log: Optional[str]`**
- **描述**: 用于保存和恢复任务进度的文件路径。
- **YAML**: `log`
- **CLI**: `--log` / `-l`
- **默认值**: `None`

**`dry_run: bool`**
- **描述**: 空跑模式。执行所有准备步骤但不实际发送网络请求。用于测试配置是否正确。
- **YAML**: `dry_run`
- **CLI**: `--dry_run`
- **默认值**: `False`

**`verbose: bool`**
- **描述**: 启用详细输出模式，显示更多调试信息。
- **YAML**: `verbose`
- **CLI**: `--verbose` / `-v`
- **环境变量**: `WEBLOGINBRUTE_VERBOSE`
- **默认值**: `False` 