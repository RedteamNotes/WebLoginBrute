# WebLoginBrute

一个专业的Web登录暴力破解工具，具有高级安全特性和性能优化功能。

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

### 环境变量配置

创建 `.env` 文件以提高安全性：

```bash
# 复制示例文件
cp env.example .env

# 编辑配置
nano .env
```

主要环境变量：

```bash
# 安全配置
WEBLOGINBRUTE_SECRET=your-super-secret-key-here
WEBLOGINBRUTE_ENCRYPTION_KEY=your-32-character-encryption-key

# 性能配置
WEBLOGINBRUTE_TIMEOUT=30
WEBLOGINBRUTE_THREADS=10
WEBLOGINBRUTE_MAX_MEMORY_MB=1024

# 安全级别
WEBLOGINBRUTE_SECURITY_LEVEL=standard
WEBLOGINBRUTE_ENABLE_HEALTH_CHECK=true
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

## 📁 项目结构

```
WebLoginBrute/
├── webloginbrute/          # 核心代码
│   ├── __init__.py
│   ├── cli.py              # 命令行界面
│   ├── config.py           # 配置管理
│   ├── core.py             # 核心引擎
│   ├── http_client.py      # HTTP客户端
│   ├── health_check.py     # 健康检查
│   ├── logger.py           # 日志管理
│   ├── performance_monitor.py  # 性能监控
│   ├── memory_manager.py   # 内存管理
│   ├── session_manager.py  # 会话管理
│   └── security.py         # 安全功能
├── tests/                  # 测试文件
├── docs/                   # 文档
├── scripts/                # 脚本工具
├── examples/               # 示例文件
├── wordlists/              # 字典文件
├── reports/                # 报告输出
├── env.example             # 环境变量示例
├── config.example.yaml     # 配置文件示例
└── README.md
```

## 🔒 安全特性

- **环境变量配置**: 支持通过环境变量设置敏感配置
- **健康检查**: 实时监控系统资源和网络状态
- **会话轮换**: 智能会话管理和连接池优化
- **内存管理**: 自动内存清理和资源监控
- **安全级别**: 多级安全控制机制
- **审计日志**: 完整的操作审计记录

## 🚀 高级功能

### 会话管理

```bash
# 启用会话轮换
webloginbrute --session-rotation-interval 300 --session-lifetime 1800

# 自定义轮换策略
webloginbrute --rotation-strategy request_count
```

### 内存管理

```bash
# 设置内存限制
webloginbrute --max-memory 2048 --memory-warning-threshold 80

# 自动内存清理
webloginbrute --memory-cleanup-interval 60
```

### 健康检查

```bash
# 启用健康检查
webloginbrute --enable-health-check

# 禁用网络验证
webloginbrute --disable-network-validation
```

## 📊 输出示例

### 进度文件 (progress.json)

```json
{
  "start_time": "2024-01-01T12:00:00",
  "total_combinations": 1000,
  "current_position": 500,
  "successful_logins": [
    {
      "username": "admin",
      "password": "password",
      "timestamp": "2024-01-01T12:30:00"
    }
  ],
  "failed_attempts": 499,
  "errors": []
}
```

### 日志文件

- `webloginbrute.log`: 主日志文件
- `audit.log`: 审计日志
- `performance.log`: 性能日志
- `progress.json`: 进度文件

## 🔧 开发

### 运行测试

```bash
# 运行所有测试
python scripts/run_tests.py

# 运行单元测试
python -m unittest discover tests -v

# 代码检查
python -m flake8 webloginbrute tests

# 安全检查
python -m bandit -r webloginbrute
```

### 贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⚠️ 免责声明

本工具仅用于授权的安全测试和教育目的。使用者必须：

- 仅在获得明确授权的目标上进行测试
- 遵守相关法律法规
- 承担使用本工具的所有责任

作者不对任何滥用行为承担责任。

## 🤝 支持

- 📖 [文档](docs/)
- 🐛 [报告问题](https://github.com/RedteamNotes/WebLoginBrute/issues)
- 💬 [讨论](https://github.com/RedteamNotes/WebLoginBrute/discussions)
- 📧 邮箱: contact@redteamnotes.com

---

**WebLoginBrute** - 专业的Web登录安全测试工具
