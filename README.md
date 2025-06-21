# WebLoginBrute 0.14

为红队行动设计的Web登录暴力破解工具，具备动态CSRF Token刷新、多线程并发、断点续扫与进度保存功能；支持高并发操作、智能重试机制和多级对抗策略。

（csrfbrute.py是稳定版，建议优先使用。）

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

## 🛠️ 安装

### 系统要求
- Python 3.7+
- 支持的操作系统：Windows, macOS, Linux

### 安装依赖
```bash
pip install -r requirements.txt
```

### 依赖包
```
requests>=2.25.1
beautifulsoup4>=4.9.3
pyyaml>=5.4.1
psutil>=5.8.0 (可选，用于性能监控)
```

## 🚀 快速开始

### 基础用法
```bash
python webloginbrute.py \
    --form-url "http://target.com/login" \
    --submit-url "http://target.com/login" \
    --csrf "csrf_token" \
    --fail-string "Login failed" \
    --users users.txt \
    --passwords passwords.txt
```

### 高级用法
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
    --proxy "http://127.0.0.1:8080" \
    --delay 1.0 \
    --timeout 10.0
```
