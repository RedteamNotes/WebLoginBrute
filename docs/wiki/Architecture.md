# 架构设计 (Architecture)

WebLoginBrute 采用了现代化的模块化架构，旨在实现高度的**可维护性**、**可扩展性**和**可测试性**。其核心设计思想是"关注点分离"（Separation of Concerns），即将不同功能的代码解耦到独立的、职责单一的模块中。

## 目录结构概览

```
WebLoginBrute/
├── webloginbrute/         # 核心逻辑包
│   ├── __main__.py        # 包执行入口 (python -m webloginbrute)
│   ├── cli.py             # 命令行接口与主函数
│   ├── config.py          # 配置管理 (Pydantic模型)
│   ├── core.py            # 核心流程调度器 (WebLoginBrute类)
│   ├── exceptions.py      # 自定义异常
│   ├── health_check.py    # 启动前健康检查模块
│   ├── http_client.py     # HTTP客户端 (会话管理, 重试)
│   ├── logger.py          # 日志系统 (敏感信息脱敏)
│   ├── memory_manager.py  # 内存监控与管理
│   ├── parsers.py         # HTML/JSON解析器
│   ├── performance_monitor.py # 性能监控
│   ├── reporting.py       # 统计与报告生成
│   ├── security.py        # 安全工具 (路径验证, 域名检查)
│   ├── session_manager.py # 会话池与轮换策略
│   ├── state.py           # 状态与进度管理
│   └── wordlists.py       # 字典加载工具
│
├── docs/                  # 文档
├── tests/                 # 单元测试
├── config.example.yaml    # 配置文件模板
└── pyproject.toml         # 项目配置与依赖管理
```

## 核心模块详解

每个模块都承担着独立的职责，通过明确的接口进行协作。

- **`cli.py`**: 程序的入口，负责解析命令行参数、初始化 `Config` 对象，并调用核心流程。
- **`config.py`**: 使用 Pydantic 定义了一个强类型的 `Config` 模型，能够统一校验和管理来自命令行、YAML 文件及环境变量的配置。
- **`core.py`**: 项目的"大脑"。`WebLoginBrute` 类在这里定义，负责编排整个爆破流程：初始化依赖模块、管理并发线程池、分发任务、监控状态并触发最终报告。
- **`health_check.py`**: 在任务开始前执行一系列检查，如网络连通性、文件权限和配置有效性，以确保运行环境的健康。
- **`http_client.py`**: 封装了 `requests` 库，负责所有网络操作，并与 `SessionManager` 协作获取和管理会话。
- **`session_manager.py`**: 管理一个 `requests.Session` 池，实现了会话的创建、复用和轮换策略（如基于时间的轮换），以应对目标网站的会话限制。
- **`memory_manager.py`**: 监控当前进程的内存使用情况。当内存超出预设阈值时，可以触发清理操作或发出警告。
- **`performance_monitor.py`**: 追踪运行时性能数据，如请求速率（RPS）、成功/失败计数等。
- **`parsers.py`**: 包含一系列用于从 HTTP 响应中提取信息的纯函数，例如解析 HTML 表单以提取 CSRF Token。
- **`state.py`**: `StateManager` 负责程序的持久化状态。它高效地管理已尝试的组合，并提供线程安全的方法来保存和加载进度。
- **`reporting.py`**: 在任务结束时，从其他模块（如 `PerformanceMonitor`）收集统计数据，并生成格式化的总结报告。
- **`logger.py`**: 提供集中的日志配置，能对日志中的敏感信息（如密码）进行自动脱敏处理。
- **`wordlists.py`**: 提供加载字典文件的工具函数，使用生成器逐行读取，以高效处理大文件。
- **`security.py`**: 包含安全相关的验证函数，如路径遍历防护、域名黑白名单检查等。
- **`exceptions.py` / `constants.py` / `version.py`**: 提供自定义异常类、全局常量和项目版本信息。

## 数据流与协作方式

```mermaid
graph TD
    A[用户] -->|命令行/YAML| B(cli.py);
    B --> C{config.py};
    C --> D[WebLoginBrute (core.py)];

    subgraph "核心调度器 (core.py)"
        D -- 初始化 --> E[HealthCheck];
        D -- 初始化 --> F[HttpClient];
        D -- 初始化 --> G[StateManager];
        D -- 初始化 --> H[PerformanceMonitor];
        D -- 初始化 --> I[SessionManager];
        D -- 初始化 --> J[MemoryManager];
    end

    subgraph "执行循环 (多线程)"
        K(WorkerThread) -->|获取会话| I;
        K -->|发送请求| F;
        F -->|HTTP/S| L[目标网站];
        L -->|响应| F;
        F -->|解析| M(parsers.py);
        M -->|CSRF Token| K;
        K -->|更新状态| G;
        K -->|更新性能| H;
    end

    D -->|启动/调度| K;
    D -->|结束时生成报告| N(reporting.py);
    H -->|提供数据| N;

    style A fill:#cde4ff
    style B fill:#cde4ff
    style C fill:#cde4ff
    style D fill:#cde4ff
    style L fill:#ffcdd2
```

1.  **启动与配置**: 用户通过 `cli.py` 启动程序，`config.py` 加载并验证所有配置，创建一个 `Config` 实例。
2.  **初始化**: `cli.py` 将 `Config` 对象注入到 `WebLoginBrute` (core) 实例中。`core` 则利用该配置初始化所有需要的服务模块（如 `HttpClient`, `StateManager`, `SessionManager` 等），实现了依赖注入。
3.  **健康检查**: 在启动爆破流程前，`HealthCheck` 模块会验证环境的有效性。
4.  **执行**: `core` 启动线程池，每个工作线程执行爆破任务：
    -   通过 `SessionManager` 获取一个可用的 HTTP 会话。
    -   使用 `HttpClient` 发送登录请求。
    -   如果需要，调用 `parsers` 从响应中提取新 Token。
    -   调用 `StateManager` 记录已尝试的组合。
    -   调用 `PerformanceMonitor` 更新实时统计。
5.  **监控**: `MemoryManager` 在后台独立监控内存使用情况。
6.  **结束**: 任务完成或中断后，`core` 调用 `reporting.py` 收集所有统计数据并向用户展示最终报告。

这种清晰的模块化设计使得代码易于理解、维护和扩展。 