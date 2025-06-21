# 架构设计 (Architecture)

WebLoginBrute 采用了现代化的模块化架构，旨在实现高度的**可维护性**、**可扩展性**和**可测试性**。其核心设计思想是“关注点分离”（Separation of Concerns），即将不同功能的代码解耦到独立的、职责单一的模块中。

## 目录结构概览

```
WebLoginBrute/
├── webloginbrute/       # 核心逻辑包
│   ├── __main__.py      # 包执行入口 (python -m webloginbrute)
│   ├── cli.py           # 命令行接口与主函数
│   ├── config.py        # 配置管理 (合并命令行与文件配置)
│   ├── core.py          # 核心流程调度器 (WebLoginBrute类)
│   ├── exceptions.py    # 自定义异常
│   ├── http_client.py   # HTTP客户端 (会话池, 重试, DNS缓存)
│   ├── logger.py        # 日志系统 (脱敏, 轮转, 审计)
│   ├── parsers.py       # HTML/JSON解析器
│   ├── reporting.py     # 统计与报告模块
│   ├── security.py      # 安全工具 (路径验证等)
│   ├── state.py         # 状态与进度管理
│   └── wordlists.py     # 字典加载工具
│
├── docs/                # 文档
├── logs/                # 日志输出目录
├── config.example.yaml  # 配置文件模板
└── requirements.txt
```

## 核心模块详解

每个模块都承担着独立的职责，通过明确的接口进行协作。

- **`cli.py`**: 程序的入口，负责解析命令行参数、初始化 `Config` 对象、创建 `WebLoginBrute` 核心类的实例，并捕获顶层异常，为用户提供友好的错误提示。

- **`config.py`**: 提供一个 `Config` 类，它能统一管理来自命令行和YAML配置文件的所有参数。它负责合并配置源（命令行优先）、校验必需项、并以类型安全的方式为其他模块提供配置。

- **`core.py`**: 这是整个爆破工具的“大脑”和“指挥官”。`WebLoginBrute` 类在这里定义，它不关心如何发送HTTP请求或如何保存进度，只负责编排整个爆破流程：
  1. 初始化所有依赖模块。
  2. 加载字典和恢复进度。
  3. 创建和管理并发线程池。
  4. 将爆破任务（用户名/密码组合）分发给工作线程。
  5. 监控任务状态（成功/失败/中断）。
  6. 在任务结束时触发最终报告和资源清理。

- **`http_client.py`**: 封装了所有与网络相关的操作。`HttpClient` 类负责管理 `requests.Session` 池、处理DNS缓存以提高性能、实现带指数退避策略的请求重试逻辑，确保网络请求的健壮性。

- **`parsers.py`**: 包含一系列纯函数，用于从HTTP响应的HTML或JSON内容中提取信息，例如提取CSRF Token、检测验证码的存在等。它将核心逻辑与目标网站的具体页面结构解耦。

- **`state.py`**: `StateManager` 类专门负责程序的持久化状态。它高效地管理已尝试的组合（使用 `deque` 和 `set`），并提供线程安全的方法来保存和加载进度到JSON文件。

- **`reporting.py`**: `StatsManager` 类是一个线程安全的统计中心。它负责追踪所有运行时数据（如尝试次数、成功/失败计数、响应时间、内存使用等），并在任务结束时生成详细的格式化报告。

- **`logger.py`**: 提供一个集中的 `setup_logging` 函数，用于配置复杂的日志系统，包括对敏感信息（用户名/密码）的自动脱敏、日志文件的自动轮转（Rotating）、以及独立的常规日志和审计（Audit）日志。

- **`wordlists.py`**: 提供加载字典文件的工具函数，使用Python生成器来逐行读取，有效避免了因加载超大字典而导致的内存耗尽问题。

- **`security.py` / `exceptions.py` / `constants.py`**: 这些是基础工具模块，分别提供安全验证函数、自定义的异常类，以及全局共享的常量（如User-Agent列表）。

## 数据流与协作方式

![Data Flow Diagram](https://user-images.githubusercontent.com/12345/67890-abc-def.png)  <!-- 占位符，可替换为真实流程图 -->

1. **启动**: 用户通过`cli.py`启动程序。
2. **配置**: `cli.py` 创建 `Config` 实例，加载所有配置。
3. **初始化**: `cli.py` 将 `Config` 对象注入到 `WebLoginBrute` (core) 的构造函数中。
4. **依赖注入**: `WebLoginBrute` 在初始化时，会创建 `HttpClient`, `StateManager`, `StatsManager` 等所有它需要的服务模块，同样将 `Config` 传递给它们。
5. **执行**: `run()` 方法被调用，`WebLoginBrute` 开始调度：
   - 调用 `wordlists` 加载字典。
   - 调用 `StateManager` 恢复进度。
   - 在线程池中，每个 `_try_login` 任务会：
     - 调用 `HttpClient` 发送GET/POST请求。
     - 调用 `Parsers` 从响应中提取Token。
     - 调用 `StateManager` 记录已尝试的组合。
     - 调用 `StatsManager` 更新统计数据。
6. **结束**: 任务完成或中断后，`WebLoginBrute` 调用 `StatsManager` 打印报告，并调用 `StateManager` 保存最终进度或清理进度文件。

这种架构使得代码清晰、健壮，并且极易于未来的功能扩展和维护。 