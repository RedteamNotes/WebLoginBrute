# WebLoginBrute - 企业级Web登录暴力破解工具

**版本：0.0.14**

WebLoginBrute是一个功能强大的Web登录暴力破解工具，专为安全测试和渗透测试设计。支持有CSRF Token和无CSRF Token的登录目标。

## 📋 项目概述

WebLoginBrute 是一个企业级的 Web登录暴力破解工具，专为安全测试和渗透测试设计。该工具采用面向对象架构，具备企业级安全性和稳定性，支持多种对抗级别和智能防护机制。

### ✨ 核心特性

- **企业级安全防护**：全面的安全审计和防护机制
- **跨平台兼容性**：修复Windows兼容性问题，支持全平台运行
- **智能对抗机制**：4级对抗模式（A0-A3），自适应速率控制
- **内存优化**：智能内存管理和缓存机制
- **会话管理**：线程安全的会话池和生命周期管理
- **安全解析器**：使用安全的HTML解析器，防止XXE攻击
- **输入验证**：全面的输入清理和路径安全检查
- **审计日志**：详细的安全审计和性能监控

### 🔒 安全特性
- **XXE防护**：使用安全的HTML解析器，防止XML外部实体攻击
- **路径遍历防护**：全面的路径安全检查，防止目录遍历攻击
- **命令注入防护**：输入验证和清理，防止命令注入攻击
- **SSRF防护**：URL验证和重定向限制，防止服务器端请求伪造
- **ReDoS防护**：安全的正则表达式使用，防止正则表达式拒绝服务攻击
- **内存攻击防护**：文件大小限制和JSON解析超时保护

### 🚀 性能特性
- **多线程支持**：可配置的并发线程数（1-100）
- **智能缓存**：DNS缓存和会话池，提高性能
- **内存优化**：智能内存清理和垃圾回收
- **自适应速率**：根据目标响应自动调整请求速率
- **批量处理**：内存友好的批量任务处理

### 🎯 对抗特性
- **4级对抗模式**：
  - A0：全速爆破模式（无对抗）
  - A1：低对抗模式（基础防护）
  - A2：中对抗模式（标准防护）
  - A3：高对抗模式（高级防护）
- **智能延迟**：根据对抗级别调整延迟时间
- **频率限制检测**：自动检测和应对频率限制
- **验证码检测**：智能检测验证码防护机制

### 📊 监控特性
- **详细统计**：全面的尝试统计和错误分类
- **性能监控**：内存使用、响应时间等性能指标
- **安全审计**：独立的安全审计日志
- **进度保存**：智能进度保存和恢复机制
- **会话恢复**：Cookie会话恢复和验证

## 🛠️ 系统要求

- **Python版本**：3.7+
- **操作系统**：Windows, macOS, Linux
- **内存**：建议2GB以上
- **网络**：稳定的网络连接

## 📦 依赖包

```
requests>=2.25.1
beautifulsoup4>=4.9.3
pyyaml>=5.4.1
psutil>=5.8.0 (可选，用于性能监控)
```

## 🚀 快速开始

### 安装
```bash
git clone https://github.com/RedteamNotes/WebLoginBrute.git
cd WebLoginBrute
pip install -r requirements.txt
```

### 基础使用
```bash
python webloginbrute.py \
    --form-url "http://target.com/login" \
    --submit-url "http://target.com/login" \
    --csrf "csrf_token" \
    --fail-string "Login failed" \
    --users users.txt \
    --passwords passwords.txt
```

### 高级使用
```bash
python webloginbrute.py \
    --form-url "http://target.com/login" \
    --submit-url "http://target.com/login" \
    --csrf "csrf_token" \
    --fail-string "Login failed" \
    --users users.txt \
    --passwords passwords.txt \
    --threads 20 \
    --aggression-level A2 \
    --enable-adaptive-rate-control \
    --enable-performance-monitoring \
    --proxy "http://127.0.0.1:8080"
```

## 📊 输出示例

```
==================================================
爆破统计信息
==================================================
对抗级别: A2
总尝试次数: 1,234
成功次数: 1
超时错误: 5
连接错误: 2
HTTP错误: 3
其他错误: 1
重试次数: 8
频率限制: 2
验证码检测: 0
自适应速率: 0.85x
连续成功: 0
连续错误: 2
总耗时: 0:05:23
平均速度: 3.85 次/秒
平均响应时间: 0.234秒
峰值内存使用: 45.2MB
内存清理次数: 2
==================================================
```

## 🔒 安全说明

### 使用场景
- 授权安全测试
- 渗透测试
- 安全研究
- 漏洞评估

### 免责声明
本工具仅用于授权的安全测试和研究目的。使用者需要确保：
- 获得目标系统的明确授权
- 遵守相关法律法规
- 承担使用风险和责任

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

### 贡献指南
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📞 联系方式

- 项目主页: [GitHub Repository](https://github.com/RedteamNotes/WebLoginBrute)
- 问题反馈: [Issues](https://github.com/RedteamNotes/WebLoginBrute/issues)
- 安全报告: 请通过Issues或邮件联系

---

**⚠️ 重要提醒**: 请确保在授权范围内使用本工具，遵守相关法律法规。 