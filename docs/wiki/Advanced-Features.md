# 高级功能

**版本：0.27.1**

本文档介绍了 WebLoginBrute 的高级功能，包括断点续扫、对抗级别、进度管理等。

## 断点续扫

WebLoginBrute 支持断点续扫功能，即使程序中断也能从上次停止的地方继续。

### 启用断点续扫

```bash
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -t 10 \
  -r  # 启用断点续扫
```

### 进度文件管理

程序会自动创建进度文件 `bruteforce_progress.json`，包含：
- 已尝试的用户名密码组合
- 统计信息
- 时间戳

### 自定义进度文件

```bash
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -t 10 \
  -r \
  -g my_progress.json  # 自定义进度文件
```

## 对抗级别

WebLoginBrute 提供4个对抗级别，适应不同的目标环境。

### 级别说明

| 级别 | 名称 | 特点 | 适用场景 |
|------|------|------|----------|
| A0 | 静默模式 | 最低对抗，最快速度 | 测试环境、无防护目标 |
| A1 | 标准模式 | 平衡性能和隐蔽性 | 一般生产环境 |
| A2 | 激进模式 | 高对抗，较慢速度 | 有WAF/IPS防护 |
| A3 | 极限模式 | 最高对抗，最慢速度 | 高安全性目标 |

### 使用对抗级别

```bash
# 标准模式（默认）
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -A A1

# 激进模式
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -A A2 \
  -t 3  # 减少线程数
```

### 对抗策略详情

#### A0 (静默模式)
- 无延迟
- 最大并发
- 无频率限制检测
- 无验证码检测

#### A1 (标准模式)
- 0.5秒请求间隔
- 5个并发线程
- 基础频率限制检测
- 基础验证码检测

#### A2 (激进模式)
- 1秒请求间隔
- 3个并发线程
- 增强频率限制检测
- 增强验证码检测
- 指数退避重试

#### A3 (极限模式)
- 2秒请求间隔
- 2个并发线程
- 完整频率限制检测
- 完整验证码检测
- 会话轮换
- 短会话生命周期

## 会话管理

### Cookie 支持

```bash
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -c cookies.txt  # Mozilla格式Cookie文件
```

### 会话池优化

程序自动管理HTTP会话池：
- 复用连接减少开销
- 自动清理过期会话
- 限制内存使用

## 高级配置

### 使用配置文件

```yaml
# advanced_config.yaml
url: "https://target.com/login"
action: "https://target.com/login"
users: "users.txt"
passwords: "passwords.txt"
csrf: "csrf_token"
threads: 5
aggressive: "A2"
resume: true
log: "advanced_progress.json"
verbose: true

# 高级选项
max_retries: 3
base_delay: 1.0
session_lifetime: 300
max_session_pool_size: 100
enable_adaptive_rate_control: true
rate_adjustment_threshold: 5
```

### 运行高级配置

```bash
python -m webloginbrute --config advanced_config.yaml
```

## 性能调优

### 线程数优化

```bash
# 高性能（适合无防护目标）
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -t 20 \
  -A A0

# 平衡性能（适合一般目标）
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -t 10 \
  -A A1

# 高隐蔽性（适合有防护目标）
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -t 3 \
  -A A2
```

### 超时设置

```bash
# 网络较慢时增加超时
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -T 60  # 60秒超时
```

## 测试模式

使用 `--dry-run` 模式测试配置而不实际发送请求：

```bash
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  --dry-run \
  -v
```

## 详细日志

启用详细输出查看调试信息：

```bash
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -v  # 详细输出
```

## 安全特性

### 输入验证

程序自动验证：
- URL格式和安全性
- 文件路径安全性
- 参数类型和范围

### 敏感信息保护

- 日志中自动脱敏用户名密码
- 审计日志独立存储
- 进度文件加密存储

### 频率限制

内置频率限制保护：
- 每分钟最大请求数限制
- 自适应速率控制
- 指数退避重试

## 最佳实践

### 1. 渐进式测试

```bash
# 第一步：测试模式验证配置
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  --dry-run \
  -v

# 第二步：小规模测试
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U small_users.txt \
  -P small_passwords.txt \
  -t 5 \
  -A A1 \
  -v

# 第三步：大规模攻击
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -t 10 \
  -A A2 \
  -r \
  -g project_progress.json
```

### 2. 监控和调整

- 观察响应时间和错误率
- 根据目标反应调整对抗级别
- 监控系统资源使用

### 3. 安全考虑

- 定期清理进度文件
- 使用VPN或代理
- 遵守法律法规
- 仅测试授权目标

## 故障排除

### 常见问题

1. **程序运行缓慢**
   - 检查网络连接
   - 降低对抗级别
   - 减少线程数

2. **频繁被阻止**
   - 提高对抗级别
   - 增加请求间隔
   - 使用代理

3. **内存使用过高**
   - 减少会话池大小
   - 降低线程数
   - 定期重启程序

### 性能监控

程序提供详细的性能指标：
- 平均响应时间
- 内存使用情况
- 请求成功率
- 错误统计

## 下一步

- 学习 [**架构设计**](Architecture.md) 了解内部原理
- 查看 [**API参考**](API-Reference.md) 进行二次开发
- 阅读 [**故障排除**](Troubleshooting.md) 解决技术问题 