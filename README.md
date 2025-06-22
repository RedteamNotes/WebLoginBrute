# WebLoginBrute

**版本：0.27.1**

WebLoginBrute 是一个专为红队行动设计的 Web 登录暴力破解工具，采用模块化架构，具备企业级稳定性和安全性。

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
git clone https://github.com/your-repo/WebLoginBrute.git
cd WebLoginBrute
pip install -r requirements.txt
```

### 基本使用

```bash
# 使用命令行参数
python -m webloginbrute -u https://target/login -a https://target/login -U users.txt -P passwords.txt -t 10 -v

# 使用配置文件
python -m webloginbrute --config config.yaml -t 10 -A A2
```

### 配置文件示例

```yaml
# config.yaml
url: https://target/login
action: https://target/login
users: users.txt
passwords: passwords.txt
csrf: token
threads: 10
aggressive: A2
verbose: true
```

## 参数说明

### 必需参数
- `-u, --url`: 登录表单页面URL
- `-a, --action`: 登录表单提交URL  
- `-U, --users`: 用户名字典文件
- `-P, --passwords`: 密码字典文件

### 可选参数
- `-s, --csrf`: CSRF token字段名
- `-t, --threads`: 并发线程数 (默认: 5)
- `-A, --aggressive`: 对抗级别 A0-A3 (默认: A1)
- `-v, --verbose`: 详细输出
- `-r, --resume`: 断点续扫
- `-c, --cookie`: Cookie文件
- `-T, --timeout`: 请求超时时间 (默认: 30秒)
- `-g, --log`: 进度文件路径
- `--config`: YAML配置文件
- `--dry-run`: 测试模式

## 对抗级别

- **A0 (静默模式)**: 最低对抗，适合测试环境
- **A1 (标准模式)**: 默认级别，平衡性能和隐蔽性
- **A2 (激进模式)**: 高对抗，适合有防护的目标
- **A3 (极限模式)**: 最高对抗，适合高安全性目标

## 项目结构

```
webloginbrute/
├── __init__.py          # 包初始化
├── __main__.py          # 模块入口点
├── cli.py              # 命令行接口
├── config.py           # 配置管理
├── core.py             # 核心流程
├── http_client.py      # HTTP客户端
├── logger.py           # 日志管理
├── parsers.py          # HTML/JSON解析
├── reporting.py        # 统计报告
├── security.py         # 安全防护
├── state.py            # 状态管理
├── wordlists.py        # 字典加载
├── constants.py        # 常量定义
└── exceptions.py       # 异常定义
```

## 安全特性

- **输入验证**: 严格的URL和文件路径验证
- **路径遍历防护**: 防止访问系统敏感目录
- **命令注入检测**: 检测并阻止危险命令
- **敏感信息脱敏**: 日志中自动隐藏用户名密码
- **频率限制**: 内置请求频率控制
- **IP白名单/黑名单**: 支持IP访问控制

## 性能优化

- **会话池管理**: 复用HTTP会话，减少连接开销
- **DNS缓存**: 避免重复域名解析
- **内存管理**: 智能清理，防止内存泄漏
- **并发控制**: 可配置的线程池大小
- **指数退避**: 智能重试机制

## 日志系统

- **分级日志**: DEBUG、INFO、WARNING、ERROR
- **日志轮转**: 自动切割大文件
- **审计日志**: 独立的安全事件记录
- **敏感信息脱敏**: 自动隐藏用户名密码

## 已知限制

- 仅支持基于表单的登录
- 不支持JavaScript渲染的页面
- 不支持复杂的验证码识别
- 需要手动配置CSRF token字段名

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 免责声明

本工具仅用于授权的安全测试和渗透测试。使用者需遵守当地法律法规，不得用于非法用途。作者不承担任何因使用本工具而产生的法律责任。
