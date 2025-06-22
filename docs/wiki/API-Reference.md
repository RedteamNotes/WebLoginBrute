# API 参考 & 开发者指南

**版本：0.0.27**

本文档旨在为希望扩展WebLoginBrute功能或将其集成到自己工作流中的开发者提供指导。

## 核心设计理念

项目采用"依赖注入"的设计模式。核心的 `WebLoginBrute` 类在初始化时会接收一个 `Config` 对象，并创建所有必需的服务模块（如`HttpClient`, `StateManager`等）。这种设计使得每个模块都可以被独立替换或模拟（Mock），极大地增强了可测试性和可扩展性。

## 主要模块的公共接口

以下是开发者最可能需要交互的核心模块及其公共API。

### 1. `Config` (`config.py`)

-   **`Config()`**: 构造函数。它会自动解析命令行参数和YAML文件来填充配置属性。
-   **属性**:
    -   `form: str` - 登录表单URL
    -   `submit: str` - 登录提交URL
    -   `users: str` - 用户名字典文件
    -   `passwords: str` - 密码字典文件
    -   `csrf: Optional[str]` - CSRF token字段名
    -   `field: Optional[str]` - 额外的登录字段名
    -   `value: Optional[str]` - 额外的登录字段值
    -   `cookies: Optional[str]` - Cookie文件路径
    -   `timeout: int` - 请求超时时间（秒）
    -   `threads: int` - 并发线程数
    -   `resume: bool` - 是否从上次中断的地方继续
    -   `progress: str` - 进度文件路径
    -   `level: str` - 对抗级别
    -   `dry_run: bool` - 测试模式
    -   `verbose: bool` - 详细输出

    你可以通过编程方式创建和填充 `Config` 对象，而不是依赖命令行解析，从而将爆破器集成到你自己的脚本中。

### 2. `WebLoginBrute` (`core.py`)

这是主流程调度器。

-   **`WebLoginBrute(config: Config)`**: 构造函数。
-   **`run()`**: 启动完整的爆破流程。这是与爆破器交互的主要入口点。

### 3. `HttpClient` (`http_client.py`)

封装所有网络请求。

-   **`HttpClient(config: Config)`**: 构造函数。
-   **`get(url: str, **kwargs) -> requests.Response`**: 发送带重试和会话管理的GET请求。
-   **`post(url: str, data: dict, **kwargs) -> requests.Response`**: 发送带重试和会话管理的POST请求。
-   **`close_all_sessions()`**: 关闭并清理会话池中的所有会-话。

### 4. `StateManager` (`state.py`)

管理持久化状态。

-   **`StateManager(config: Config)`**: 构造函数。
-   **`add_attempted(combination: tuple)`**: 添加一个已尝试的组合。
-   **`has_been_attempted(combination: tuple) -> bool`**: 检查组合是否已尝试。
-   **`save_progress(stats: dict)`**: 将当前状态保存到文件。
-   **`load_progress() -> tuple`**: 从文件加载状态。
-   **`cleanup_progress_file()`**: 删除进度文件。

### 5. `StatsManager` (`reporting.py`)

管理统计信息。

-   **`StatsManager()`**: 构造函数。
-   **`update(stat_type: str, value: int = 1)`**: 线程安全地更新一个统计项。
-   **`record_response_time(response_time: float)`**: 记录一次响应耗时。
-   **`print_final_report()`**: 打印格式化的最终报告。

---

## 扩展示例

### 示例1：自定义登录成功/失败的判断逻辑

默认的成功判断逻辑在 `WebLoginBrute._check_login_success()` 中。如果你想针对特定目标进行修改，最简单的方式是继承 `WebLoginBrute` 类并重写该方法。

```python
# custom_brute.py
import requests
from webloginbrute.core import WebLoginBrute
from webloginbrute.config import Config

class MyBrute(WebLoginBrute):
    def _check_login_success(self, response: requests.Response) -> bool:
        # 针对你的目标的自定义逻辑
        # 例如，检查响应JSON中是否包含 '{"status": "ok"}'
        if response.headers.get('Content-Type') == 'application/json':
            try:
                data = response.json()
                if data.get('status') == 'ok':
                    return True
            except:
                return False
        # 如果不是JSON，回退到父类的逻辑
        return super()._check_login_success(response)

if __name__ == "__main__":
    config = Config()
    brute = MyBrute(config)
    brute.run()
```

### 示例2：集成到现有脚本中

你可以完全绕过命令行，以编程方式使用WebLoginBrute。这对于将爆破功能集成到更大型的自动化测试套件中非常有用。

由于配置现在由 `pydantic` 管理，最清晰的方式是创建一个字典，然后使用 `Config.parse_obj()` 方法来实例化和验证配置。

```python
from webloginbrute import WebLoginBrute, Config

# 创建配置
config = Config(
    form="https://redteamnotes.com/login",
    submit="https://redteamnotes.com/login/authenticate",
    users="wordlists/users.txt",  # 确保这个路径是正确的
    passwords="wordlists/passwords.txt", # 确保这个路径是正确的
    csrf="csrf_token",
    threads=10,
    level="A1"
)

# 创建爆破器实例
brute = WebLoginBrute(config)

# 开始攻击
brute.run()
```

这个API参考为你提供了与WebLoginBrute核心组件交互和扩展其功能的基础。 