# WebLoginBrute API 参考文档

## 概述

WebLoginBrute 是一个专业的Web登录暴力破解工具，提供完整的API接口用于自动化安全测试。

## 核心模块

### Config 类

配置管理类，负责处理所有配置参数。

#### 构造函数

```python
Config(
    url: str,                    # 登录表单页面URL
    action: str,                 # 登录表单提交URL
    users: str,                  # 用户名字典文件路径
    passwords: str,              # 密码字典文件路径
    csrf: Optional[str] = None,  # CSRF token字段名
    login_field: Optional[str] = None,  # 额外的登录字段名
    login_value: Optional[str] = None,  # 额外的登录字段值
    cookie: Optional[str] = None,       # Cookie文件路径
    timeout: int = 30,           # 请求超时时间（秒）
    threads: int = 5,            # 并发线程数
    resume: bool = False,        # 从上次中断的地方继续
    log: Optional[str] = None,   # 进度文件路径
    aggressive: int = 1,         # 对抗级别
    dry_run: bool = False,       # 测试模式
    verbose: bool = False,       # 详细输出
    **kwargs                     # 其他配置参数
)
```

#### 主要属性

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `url` | str | 必需 | 登录表单页面URL |
| `action` | str | 必需 | 登录表单提交URL |
| `users` | str | 必需 | 用户名字典文件路径 |
| `passwords` | str | 必需 | 密码字典文件路径 |
| `timeout` | int | 30 | 请求超时时间（秒） |
| `threads` | int | 5 | 并发线程数 |
| `max_memory_mb` | int | 1024 | 最大内存使用量(MB) |
| `security_level` | str | 'standard' | 安全级别 |

#### 验证方法

```python
def validate_urls(self) -> None
def validate_files(self) -> None
def validate_security(self) -> None
```

### WebLoginBrute 类

主要的暴力破解引擎类。

#### 构造函数

```python
WebLoginBrute(config: Config)
```

#### 主要方法

##### `run() -> Dict[str, Any]`

执行暴力破解攻击。

**返回值:**
```python
{
    'success': bool,           # 是否成功完成
    'total_attempts': int,     # 总尝试次数
    'successful_logins': List[Dict],  # 成功的登录信息
    'failed_attempts': int,    # 失败尝试次数
    'duration': float,         # 执行时间（秒）
    'errors': List[str]        # 错误信息列表
}
```

##### `stop() -> None`

停止暴力破解攻击。

##### `pause() -> None`

暂停暴力破解攻击。

##### `resume() -> None`

恢复暴力破解攻击。

#### 事件回调

```python
def on_login_attempt(self, username: str, password: str, success: bool) -> None
def on_progress(self, current: int, total: int) -> None
def on_error(self, error: Exception) -> None
```

### HttpClient 类

HTTP客户端类，负责处理网络请求。

#### 构造函数

```python
HttpClient(
    timeout: int = 30,
    max_retries: int = 3,
    user_agent: str = "WebLoginBrute/0.27.2"
)
```

#### 主要方法

##### `get(url: str, **kwargs) -> Response`

发送GET请求。

##### `post(url: str, data: Dict, **kwargs) -> Response`

发送POST请求。

##### `resolve_host(hostname: str) -> Optional[str]`

解析主机名。

##### `close_all_sessions() -> None`

关闭所有会话。

### 异常类

#### BruteForceError

暴力破解过程中的基础异常。

```python
class BruteForceError(Exception):
    def __init__(self, message: str, error_code: Optional[str] = None)
```

#### ConfigurationError

配置错误异常。

```python
class ConfigurationError(BruteForceError):
    def __init__(self, message: str, field_name: Optional[str] = None)
```

#### RateLimitError

速率限制异常。

```python
class RateLimitError(BruteForceError):
    def __init__(self, message: str, retry_after: Optional[int] = None)
```

#### MemoryError

内存错误异常。

```python
class MemoryError(BruteForceError):
    def __init__(self, message: str, memory_usage: Optional[float] = None)
```

## 增强模块

### HealthCheck 类

系统健康检查模块。

```python
class HealthCheck:
    def __init__(self, config: Config)
    
    def check_system_resources(self) -> HealthCheckResult
    def check_network_connectivity(self) -> HealthCheckResult
    def check_file_integrity(self) -> HealthCheckResult
    def run_full_check(self) -> List[HealthCheckResult]
```

### PerformanceMonitor 类

性能监控模块。

```python
class PerformanceMonitor:
    def __init__(self, config: Config)
    
    def start_monitoring(self) -> None
    def stop_monitoring(self) -> None
    def get_performance_stats(self) -> Dict[str, Any]
    def log_performance_event(self, event_type: str, data: Dict) -> None
```

### MemoryManager 类

内存管理模块。

```python
class MemoryManager:
    def __init__(self, config: Config)
    
    def check_memory_usage(self) -> float
    def cleanup_memory(self) -> None
    def is_memory_critical(self) -> bool
    def get_memory_stats(self) -> Dict[str, Any]
```

### SessionManager 类

会话管理模块。

```python
class SessionManager:
    def __init__(self, config: Config)
    
    def get_session(self) -> requests.Session
    def return_session(self, session: requests.Session) -> None
    def rotate_sessions(self) -> None
    def get_session_stats(self) -> Dict[str, Any]
```

## 使用示例

### 基本用法

```python
from webloginbrute import Config, WebLoginBrute

# 创建配置
config = Config(
    url="https://example.com/login",
    action="https://example.com/auth",
    users="users.txt",
    passwords="passwords.txt",
    threads=10,
    timeout=30
)

# 创建暴力破解实例
brute = WebLoginBrute(config)

# 执行攻击
result = brute.run()
print(f"成功登录: {len(result['successful_logins'])}")
```

### 高级用法

```python
from webloginbrute import Config, WebLoginBrute
from webloginbrute.health_check import HealthCheck

# 创建配置
config = Config(
    url="https://example.com/login",
    action="https://example.com/auth",
    users="users.txt",
    passwords="passwords.txt",
    enable_health_check=True,
    security_level="high"
)

# 健康检查
health_checker = HealthCheck(config)
health_results = health_checker.run_full_check()

# 检查健康状态
if any(not result.success for result in health_results):
    print("系统健康检查失败")
    return

# 执行暴力破解
brute = WebLoginBrute(config)
result = brute.run()
```

### 事件处理

```python
class CustomBruteForce(WebLoginBrute):
    def on_login_attempt(self, username: str, password: str, success: bool):
        if success:
            print(f"✅ 成功登录: {username}:{password}")
        else:
            print(f"❌ 登录失败: {username}:{password}")
    
    def on_progress(self, current: int, total: int):
        percentage = (current / total) * 100
        print(f"进度: {percentage:.1f}% ({current}/{total})")

# 使用自定义类
brute = CustomBruteForce(config)
result = brute.run()
```

## 环境变量

WebLoginBrute 支持通过环境变量进行配置：

| 环境变量 | 默认值 | 描述 |
|----------|--------|------|
| `WEBLOGINBRUTE_SECRET` | 临时生成 | 安全密钥 |
| `WEBLOGINBRUTE_TIMEOUT` | 30 | 请求超时时间 |
| `WEBLOGINBRUTE_THREADS` | 5 | 并发线程数 |
| `WEBLOGINBRUTE_MAX_MEMORY_MB` | 1024 | 最大内存使用量 |
| `WEBLOGINBRUTE_SECURITY_LEVEL` | standard | 安全级别 |
| `WEBLOGINBRUTE_VERBOSE` | false | 详细输出 |

## 错误处理

```python
from webloginbrute import BruteForceError, ConfigurationError, RateLimitError

try:
    brute = WebLoginBrute(config)
    result = brute.run()
except ConfigurationError as e:
    print(f"配置错误: {e}")
except RateLimitError as e:
    print(f"速率限制: {e}, 等待 {e.retry_after} 秒")
except BruteForceError as e:
    print(f"暴力破解错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 最佳实践

1. **配置验证**: 始终验证配置参数
2. **错误处理**: 使用适当的异常处理
3. **资源管理**: 及时清理资源
4. **日志记录**: 启用详细日志记录
5. **安全考虑**: 使用适当的安全级别
6. **性能监控**: 监控系统资源使用情况 