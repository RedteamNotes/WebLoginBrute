# WebLoginBrute 0.27

为红队行动设计的Web登录暴力破解工具，具备动态CSRF Token刷新、多线程并发、断点续扫与进度保存功能；支持高并发操作、智能重试机制和多级对抗策略。

---

## :sparkles: 功能特性

- **:package: 现代化模块化架构**: 代码完全重构，职责分离，易于维护、扩展和二次开发。
- **:rocket: 高并发性能**: 基于 `ThreadPoolExecutor` 的多线程并发模型，提供高效的爆破速度。
- **:zap: 智能进度管理**: 自动保存和恢复爆破进度，即使程序中断，也能无缝继续，避免重复工作。
- **:shield: 强大的对抗性**:
  - 支持有/无 CSRF Token 的登录场景，并能自动刷新Token。
  - 内置多种对抗级别 (`A0` 到 `A3`)，可调整攻击的隐蔽性与速率。
  - 动态调整请求速率，模拟真实用户行为，规避WAF/IPS检测。
- **:wrench: 灵活的配置选项**: 支持命令行参数和外部 `YAML` 配置文件两种方式，满足不同场景下的使用需求。
- **:scroll: 详细的统计报告**: 任务结束后生成全面的统计报告，包括总耗时、平均速率、成功/失败详情、性能指标等。
- **:lock: 安全第一**:
  - 内置路径遍历、命令注入等安全检查。
  - 自动脱敏日志和报告中的敏感信息（用户名/密码）。
  - 提供IP白名单/黑名单功能，确保攻击目标的准确性。
- **:microscope: 测试与调试**:
  - 提供 `--dry-run` 模式，用于测试配置和流程，而不实际发送攻击请求。
  - 提供 `--verbose` 模式，输出详细的调试日志。

---

## :gear: 安装

1.  创建并激活虚拟环境（推荐标准做法）:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Windows下为 venv\Scripts\activate
    ```

2.  安装依赖:
    ```bash
    pip install -r requirements.txt
    ```

---

## :fast_forward: 快速开始

WebLoginBrute可以通过两种方式进行配置：**命令行参数**或**YAML配置文件**。

### 方式一：使用命令行参数 (推荐用于快速测试)

```bash
python -m webloginbrute \
    --form-url "https://redteamnotes.com/login" \
    --submit-url "https://redteamnotes.com/login/authenticate" \
    --username-file "wordlists/users.txt" \
    --password-file "wordlists/passwords.txt" \
    --csrf "csrf_token" \
    --threads 10 \
    --verbose
```

### 方式二：使用YAML配置文件 (推荐用于复杂场景)

1.  创建一个 `config.yaml` 文件 (可以从 `config.example.yaml` 复制和修改)。

    ```yaml
    # config.yaml
    form_url: "https://redteamnotes.com/login"
    submit_url: "https://redteamnotes.com/login/authenticate"
    username_file: "wordlists/users.txt"
    password_file: "wordlists/passwords.txt"
    csrf: "csrf_token"
    threads: 10
    timeout: 20
    verbose: true
    # 更多高级配置...
    ```

2.  运行程序并指定配置文件:
    ```bash
    python -m webloginbrute --config-file config.yaml
    ```

---

## :books: 文档

需要更详细的信息吗？请查阅我们的 **[Wiki 文档](docs/wiki/Home.md)**，你可以在那里找到：

-   [**配置详解**](docs/wiki/Configuration.md): 所有配置项的详细说明。
-   [**架构设计**](docs/wiki/Architecture.md): 深入了解工具的内部工作原理。
-   [**高级功能**](docs/wiki/Advanced-Features.md): 如何使用对抗级别、进度恢复等高级功能。
-   [**API参考 (开发者)**](docs/wiki/API-Reference.md): 如何基于新架构进行二次开发。

---

## :warning: 已知局限性

- **无法处理JavaScript渲染的验证码**: 本工具的验证码检测基于HTML关键字和简单元素，无法处理由JS动态加载或渲染的复杂验证码（如reCAPTCHA, hCaptcha）。
- **WAF/IPS绕过能力有限**: 对抗级别和动态延迟能规避部分WAF策略，但无法保证绕过所有高级WAF的行为分析和指纹识别。
- **不支持多步登录**: 当前版本仅支持单次POST请求的登录流程，不支持需要多次跳转、JS计算或扫码的多步登录。

---

## :warning: 免责声明

本工具仅供授权的渗透测试和安全研究使用。任何未经授权的、非法的攻击行为，开发者不承担任何责任。请遵守当地法律法规。
