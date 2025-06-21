# 快速入门指南

**版本：0.0.27**

本指南将帮助你快速安装并运行WebLoginBrute。

## 1. 环境要求

- Python 3.8+
- 支持的操作系统: Windows, macOS, Linux

## 2. 安装

首先，克隆项目的最新版本到你的本地机器：

```bash
git clone https://github.com/your-repo/WebLoginBrute.git
cd WebLoginBrute
```

然后，创建并激活虚拟环境（标准做法）：

```bash
python3 -m venv venv
source venv/bin/activate  # Windows下为 venv\Scripts\activate
```

安装所有必需的Python依赖包：

```bash
pip install -r requirements.txt
```

现在，WebLoginBrute已经准备就绪！

## 3. 准备工作

在开始爆破之前，你需要准备两样东西：

-   **目标信息**:
    -   登录表单页面的URL (`--form-url`)
    -   表单提交的目标URL (`--submit-url`)
-   **字典文件**:
    -   一个包含用户名的文本文件 (`--username-file`)
    -   一个包含密码的文本文件 (`--password-file`)

## 4. 运行你的第一次爆破

你可以通过提供最核心的命令行参数来快速启动一次爆破任务。

```bash
python -m webloginbrute \
    --form-url "https://redteamnotes.com/login" \
    --submit-url "https://redteamnotes.com/login/authenticate" \
    --username-file "wordlists/users.txt" \
    --password-file "wordlists/passwords.txt"
```

程序将会启动，并使用默认的配置（例如5个并发线程）开始爆破。

## 5. 查看结果

任务运行期间，你会在控制台看到实时的进度信息。任务结束后，会打印一份详细的统计报告，如下所示：

```
==================================================
                暴力破解任务完成
==================================================
 概要信息
   - 总耗时: 123.45 秒
   - 总尝试次数: 1000
   - 平均速率: 8.10 次/秒
--------------------------------------------------
 结果分析
   - 成功破解: 1
   - 遭遇频率限制: 5
   - 检测到验证码: 0
--------------------------------------------------
 错误统计
   - 超时错误: 2
   - 连接错误: 1
   - HTTP错误: 0
   - 其他错误: 0
   - 内部重试: 8
--------------------------------------------------
 性能指标
   - 平均响应时间: 0.150 秒
   - 峰值内存使用: 45.67 MB
==================================================
```

同时，在项目根目录下会生成一个 `logs/` 目录，其中包含了本次任务的详细日志文件和审计日志文件。

## 下一步

恭喜你完成了第一次爆破！现在你可以探索更高级的功能了：

-   学习如何使用 **[YAML配置文件](Configuration.md)** 来管理复杂的任务。
-   了解不同的 **[高级功能](Advanced-Features.md)**，例如对抗级别和进度恢复。
-   深入探索项目的 **[架构设计](Architecture.md)**。 