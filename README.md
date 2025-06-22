# WebLoginBrute 0.27

为红队行动设计的Web登录暴力破解工具，具备动态CSRF Token刷新、多线程并发、断点续扫与进度保存功能；支持高并发操作、智能重试机制和多级对抗策略。

## 特性

- 🚀 **模块化架构**：清晰的代码结构，易于扩展和维护
- 🔒 **安全防护**：内置输入验证、路径遍历防护、命令注入检测
- 🎯 **智能对抗**：多级对抗策略，支持 CSRF Token 动态刷新
- ⚡ **高性能**：多线程并发、会话池管理、DNS 缓存优化
- 📊 **详细统计**：实时进度监控、性能指标、审计日志
- 🔄 **断点续扫**：智能进度保存与恢复，避免重复爆破
- 🛡️ **企业级稳定**：完善的异常处理、优雅退出机制

## 快速开始

### 安装

```bash
# 从PyPI安装
pip install webloginbrute

# 或从源码安装
git clone https://github.com/RedteamNotes/WebLoginBrute.git
cd WebLoginBrute
pip install -r requirements.txt
```

### 基本使用

```bash
# 使用命令行参数
webloginbrute -u https://redteamnotes.com/login -a https://redteamnotes.com/login/authenticate -U users.txt -P passwords.txt -t 10 --verbose

# 使用配置文件
webloginbrute --config config.yaml -t 10 -A 2
```

### 配置文件示例

```yaml
# WebLoginBrute v0.27.2 配置文件示例
# 复制此文件为 config.yaml 并根据需要修改

# ⚠️ 切勿将真实密码、cookie等敏感信息直接写入此文件！
# 建议将敏感信息通过安全方式管理，如环境变量或专用密钥管理系统。

# 必需参数
url: "https://redteamnotes.com/login"                    # 登录表单页面URL
action: "https://redteamnotes.com/login/authenticate"    # 登录表单提交URL
users: "wordlists/users.txt"                       # 用户名字典文件
passwords: "wordlists/passwords.txt"               # 密码字典文件

# 结果判断参数 (至少需要一个)
success_string: "Welcome"
fail_string: "Invalid credentials"
# success_redirect: "https://redteamnotes.com/dashboard"
# failure_redirect: "https://redteamnotes.com/login?error=1"

# 可选参数
csrf: "csrf_token"                                 # CSRF token字段名（如目标无CSRF token可省略）
login_field: "domain"                              # 额外的登录字段名（可选）
login_value: "example.com"                         # 额外的登录字段值（可选）
cookie: "cookies.txt"                              # Cookie文件路径（可选）

# 性能配置
threads: 5                                         # 并发线程数 (1-100)
timeout: 30                                        # 请求超时时间（秒）
aggressive: 1                                   # 对抗级别: 0(静默) 1(标准) 2(激进) 3(极限)

# 进度管理
resume: false                                      # 是否从上次中断的地方继续
log: "bruteforce_progress.json"                    # 进度文件路径

# 输出控制
verbose: false                                     # 详细输出模式
dry_run: false                                     # 测试模式，不实际发送请求

# 高级配置（可选）
# max_retries: 3                                   # 最大重试次数
# base_delay: 1.0                                  # 基础延迟时间（秒）
# session_lifetime: 300                            # 会话生命周期（秒）
# max_session_pool_size: 100                       # 最大会话池大小
# enable_adaptive_rate_control: true               # 启用自适应速率控制
# rate_adjustment_threshold: 5                     # 速率调整阈值

# 安全配置（可选）
# ip_whitelist: ["192.168.1.0/24"]                # IP白名单
# ip_blacklist: ["10.0.0.1"]                      # IP黑名单
```

## 高级功能

### 对抗级别

- **0 (静默模式)**: 最低对抗，最快速度，适合测试环境
- **1 (标准模式)**: 平衡性能和隐蔽性，默认级别
- **2 (激进模式)**: 高对抗，较慢速度，适合有WAF的目标
- **3 (极限模式)**: 最高对抗，最慢速度，适合高安全性目标

### 断点续扫

```bash
# 启动任务
webloginbrute --config config.yaml --resume

# 中断后继续
webloginbrute --config config.yaml --resume
```

### 自定义成功判定

```python
# 在代码中自定义成功/失败关键字
success_keywords = ["dashboard", "welcome", "logout", "profile"]
failure_keywords = ["invalid", "incorrect", "failed", "error"]

# 调用时传入自定义关键字
result = self._check_login_success(
    response, 
    success_keywords=success_keywords,
    failure_keywords=failure_keywords
)
```

## 文档

详细文档请访问：[Wiki](https://github.com/RedteamNotes/WebLoginBrute/wiki)

- [快速开始](https://github.com/RedteamNotes/WebLoginBrute/wiki/Getting-Started)
- [配置详解](https://github.com/RedteamNotes/WebLoginBrute/wiki/Configuration)
- [高级功能](https://github.com/RedteamNotes/WebLoginBrute/wiki/Advanced-Features)
- [故障排除](https://github.com/RedteamNotes/WebLoginBrute/wiki/Troubleshooting)

## 开发

### 环境设置

```bash
# 运行开发环境设置脚本
python setup_dev.py

# 或手动设置
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 运行测试

```bash
# 运行所有测试
python run_tests.py

# 或使用pytest
pytest tests/

# 生成覆盖率报告
coverage run -m pytest tests/
coverage report
coverage html
```

### 代码质量

```bash
# 代码格式化
black webloginbrute tests/

# 导入排序
isort webloginbrute tests/

# 代码检查
flake8 webloginbrute tests/

# 安全检查
bandit -r webloginbrute/

# 类型检查
mypy webloginbrute/
```

### 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 免责声明

本工具仅用于授权的安全测试和教育目的。使用者需要确保在合法授权的情况下使用，作者不承担任何法律责任。
