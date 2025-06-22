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
git clone https://github.com/RedteamNotes/WebLoginBrute.git
cd WebLoginBrute
pip install -r requirements.txt
```

### 基本使用

```bash
# 使用命令行参数
webloginbrute -u https://redteamnotes.com/login -a https://redteamnotes.com/login/authenticate -U users.txt -P passwords.txt -t 10 -w

# 使用配置文件
webloginbrute --config config.yaml -t 10 -A A2
```

### 配置文件示例

```