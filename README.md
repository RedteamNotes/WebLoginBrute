# WebLoginBrute 0.27

[![LICENSE](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![Release](https://img.shields.io/github/v/release/RedteamNotes/WebLoginBrute.svg)](https://github.com/RedteamNotes/WebLoginBrute/releases)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/RedteamNotes/WebLoginBrute/badge)](https://securityscorecards.dev/viewer/?uri=github.com/RedteamNotes/WebLoginBrute)

为红队行动设计的Web登录暴力破解工具，具备动态CSRF Token刷新、多线程并发、断点续扫与进度保存功能；支持高并发操作、智能重试机制和多级对抗策略。

（开发中，不建议使用，csrfbrute.py 是精简化稳定版本）

## ✨ 特性

- 🔒 **高级安全特性**: 支持多种安全级别和防护机制
- ⚡ **高性能**: 多线程并发，智能内存管理
- 🛡️ **健康检查**: 实时系统资源监控和网络连通性验证
- 📊 **详细报告**: 完整的测试报告和性能统计
- 🔧 **灵活配置**: 支持命令行参数、配置文件和环境变量
- 📝 **完整日志**: 结构化日志记录和审计功能
- 🔄 **会话管理**: 智能会话轮换和连接池管理
- 🚀 **易于使用**: 简洁的CLI界面和丰富的API

## 🚀 快速开始

### 安装

```bash
# 从源码安装
git clone https://github.com/RedteamNotes/WebLoginBrute.git
cd WebLoginBrute
pip install -e .

# 或使用 pip 安装
pip install webloginbrute
```

### 基本使用

```bash
# 最简单的用法
webloginbrute -u https://redteamnotes.com/login -a https://redteamnotes.com/auth -U users.txt -P passwords.txt

# 使用配置文件
webloginbrute --config config.yaml

# 详细输出模式
webloginbrute -u https://redteamnotes.com/login -a https://redteamnotes.com/auth -U users.txt -P passwords.txt --verbose
```

## 📚 文档

- [用户指南](docs/User-Guide.md) - 详细的使用说明和最佳实践
- [API参考](docs/API-Reference.md) - 完整的API文档和示例
- [配置说明](docs/Configuration.md) - 配置选项详解
- [高级功能](docs/Advanced-Features.md) - 高级特性和自定义选项
- [常见问题](docs/FAQ.md) - 故障排除和常见问题解答

## 🔧 配置选项

### 命令行参数

| 参数 | 短参数 | 描述 | 示例 |
|------|--------|------|------|
| `--url` | `-u` | 登录表单页面URL | `https://redteamnotes.com/login` |
| `--action` | `-a` | 登录表单提交URL | `https://redteamnotes.com/auth` |
| `--users` | `-U` | 用户名字典文件 | `users.txt` |
| `--passwords` | `-P` | 密码字典文件 | `passwords.txt` |
| `--csrf` | `-s` | CSRF token字段名 | `csrf_token` |
| `--timeout` | `-T` | 请求超时时间（秒） | `30` |
| `--threads` | `-t` | 并发线程数 | `10` |
| `--aggressive` | `-A` | 对抗级别 | `2` |
| `--verbose` | | 详细输出 | |
| `--dry-run` | | 测试模式 | |

### 对抗级别

| 级别 | 描述 | 特点 |
|------|------|------|
| 0 | 静默模式 | 最小化网络活动，适合隐蔽测试 |
| 1 | 标准模式 | 平衡性能和隐蔽性 |
| 2 | 激进模式 | 高并发，快速测试 |
| 3 | 极限模式 | 最大并发，可能触发防护 |

### 安全级别

| 级别 | 描述 | 特点 |
|------|------|------|
| low | 低安全级别 | 最小安全检查，适合测试环境 |
| standard | 标准安全级别 | 平衡安全性和性能 |
| high | 高安全级别 | 严格安全检查，适合生产环境 |
| paranoid | 偏执安全级别 | 最高安全检查，可能影响性能 |

## ⚠️ 免责声明和许可证

本工具仅用于授权的安全测试和教育目的。使用者必须：仅在获得明确授权的目标上进行测试、遵守相关法律法规、承担使用本工具的所有责任，作者不对任何滥用行为承担责任。本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。
