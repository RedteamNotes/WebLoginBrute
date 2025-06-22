# 对抗级别

WebLoginBrute提供四级对抗策略，用户可根据目标安全级别选择合适的攻击强度。

## 🎯 对抗级别概述

| 级别 | 名称 | 适用场景 | 延迟范围 | 检测功能 | 会话管理 |
|------|------|----------|----------|----------|----------|
| A0 | 全速爆破 | 无防护目标 | 0-0.1秒 | 关闭 | 关闭 |
| A1 | 低对抗 | 基础防护 | 0.5-2秒 | 基础 | 关闭 |
| A2 | 中对抗 | 中等安全 | 1-5秒 | 完整 | 启用 |
| A3 | 高对抗 | 高安全 | 2-10秒 | 完整 | 高级 |

## 🚀 A0 - 全速爆破模式

### 特点
- **无任何延迟** - 最大速度爆破
- **关闭所有检测** - 不检测频率限制和验证码
- **简化会话管理** - 每次请求创建新会话
- **最高性能** - 适合大规模字典测试

### 适用场景
- 无防护或简单防护的目标
- 内部测试环境
- 需要快速验证的目标
- 字典文件较小的情况

### 配置参数

```yaml
aggressive: "A0"

# 自动设置的参数
min_delay: 0.0
max_delay: 0.1
jitter_factor: 0.0
enable_smart_delay: false
enable_session_pool: false
enable_rate_limit_detection: false
enable_captcha_detection: false
session_lifetime: 0
```

### 使用示例

```yaml
# 快速爆破配置
url: "https://test.example.com/login"
success_redirect: "https://test.example.com/dashboard"
failure_redirect: "https://test.example.com/login"
users: "users.txt"
passwords: "passwords.txt"
threads: 20
aggressive: "A0"
```

### 性能特点
- **速度**: 最高 (50-100 次/秒)
- **资源消耗**: 最低
- **成功率**: 依赖目标防护
- **风险**: 容易被检测

## 🛡️ A1 - 低对抗模式

### 特点
- **基础延迟** - 模拟人类输入速度
- **基础检测** - 检测频率限制和验证码
- **简单会话** - 不启用会话池
- **平衡性能** - 速度与隐蔽性平衡

### 适用场景
- 基础防护目标
- 简单的WAF防护
- 需要一定隐蔽性的测试
- 中等规模字典测试

### 配置参数

```yaml
aggressive: "A1"

# 自动设置的参数
min_delay: 0.5
max_delay: 2.0
jitter_factor: 0.2
enable_smart_delay: true
enable_session_pool: false
enable_rate_limit_detection: true
enable_captcha_detection: true
session_lifetime: 60
```

### 使用示例

```yaml
# 低对抗配置
url: "https://example.com/login"
success_redirect: "https://example.com/dashboard"
failure_redirect: "https://example.com/login"
users: "users.txt"
passwords: "passwords.txt"
threads: 10
aggressive: "A1"
```

### 性能特点
- **速度**: 中等 (10-30 次/秒)
- **资源消耗**: 低
- **成功率**: 较高
- **风险**: 中等

## ⚔️ A2 - 中对抗模式

### 特点
- **标准延迟** - 更真实的人类行为模拟
- **完整检测** - 全面的防护机制检测
- **会话池管理** - 智能会话复用
- **高级仿真** - 模拟真实浏览器行为

### 适用场景
- 中等安全目标
- 有WAF防护的系统
- 企业级应用测试
- 需要高隐蔽性的操作

### 配置参数

```yaml
aggressive: "A2"

# 自动设置的参数
min_delay: 1.0
max_delay: 5.0
jitter_factor: 0.3
enable_smart_delay: true
enable_session_pool: true
enable_rate_limit_detection: true
enable_captcha_detection: true
session_lifetime: 300
```

### 使用示例

```yaml
# 中对抗配置
url: "https://secure.example.com/login"
success_redirect: "https://secure.example.com/dashboard"
failure_redirect: "https://secure.example.com/login"
users: "users.txt"
passwords: "passwords.txt"
threads: 5
aggressive: "A2"
proxy: "http://127.0.0.1:8080"
```

### 性能特点
- **速度**: 中低 (5-15 次/秒)
- **资源消耗**: 中等
- **成功率**: 高
- **风险**: 低

## 🛡️ A3 - 高对抗模式

### 特点
- **高级延迟** - 最长的人类行为模拟
- **完整防护** - 最全面的检测和处理
- **高级会话管理** - 长时间会话保持
- **最大隐蔽性** - 最难被检测

### 适用场景
- 高安全目标
- 有高级WAF的系统
- 政府或金融机构
- 需要最高隐蔽性的操作

### 配置参数

```yaml
aggressive: "A3"

# 自动设置的参数
min_delay: 2.0
max_delay: 10.0
jitter_factor: 0.5
enable_smart_delay: true
enable_session_pool: true
enable_rate_limit_detection: true
enable_captcha_detection: true
session_lifetime: 600
```

### 使用示例

```yaml
# 高对抗配置
url: "https://bank.example.com/login"
success_redirect: "https://bank.example.com/dashboard"
failure_redirect: "https://bank.example.com/login"
users: "users.txt"
passwords: "passwords.txt"
threads: 3
aggressive: "A3"
proxy: "http://proxy.example.com:8080"
min_delay: 3.0
max_delay: 15.0
```

### 性能特点
- **速度**: 最低 (2-8 次/秒)
- **资源消耗**: 高
- **成功率**: 最高
- **风险**: 最低

## 🔄 级别切换策略

### 渐进式升级

```yaml
# 1. 先用A0快速测试
aggressive: "A0"
threads: 20

# 2. 如果被检测，升级到A1
aggressive: "A1"
threads: 10

# 3. 如果仍有问题，升级到A2
aggressive: "A2"
threads: 5

# 4. 最后使用A3
aggressive: "A3"
threads: 3
```

### 自适应策略

```bash
# 监控输出，根据检测情况调整
# 如果看到频率限制警告，降低级别
# 如果看到验证码检测，提高级别
```

## 📊 性能对比

| 指标 | A0 | A1 | A2 | A3 |
|------|----|----|----|----|
| 平均速度(次/秒) | 50-100 | 10-30 | 5-15 | 2-8 |
| 内存使用 | 低 | 低 | 中 | 高 |
| CPU使用 | 低 | 低 | 中 | 高 |
| 网络流量 | 高 | 中 | 中 | 低 |
| 检测风险 | 高 | 中 | 低 | 很低 |
| 成功率 | 依赖防护 | 较高 | 高 | 最高 |

## 🛠️ 自定义配置

### 覆盖默认值

```yaml
# 使用A2级别但自定义延迟
aggressive: "A2"
min_delay: 0.5      # 覆盖默认的1.0
max_delay: 3.0      # 覆盖默认的5.0
jitter_factor: 0.5  # 覆盖默认的0.3
```

### 混合策略

```yaml
# 使用A1级别但启用会话池
aggressive: "A1"
enable_session_pool: true  # 覆盖默认的false
session_lifetime: 300      # 覆盖默认的60
```

## 🎯 选择建议

### 根据目标类型选择

| 目标类型 | 推荐级别 | 理由 |
|----------|----------|------|
| 测试环境 | A0 | 无防护，追求速度 |
| 小型网站 | A1 | 基础防护，平衡性能 |
| 企业应用 | A2 | 中等防护，需要隐蔽 |
| 金融机构 | A3 | 高级防护，最高隐蔽 |

### 根据字典大小选择

| 字典大小 | 推荐级别 | 线程数 |
|----------|----------|--------|
| < 1000 | A0 | 20 |
| 1000-10000 | A1 | 10 |
| 10000-100000 | A2 | 5 |
| > 100000 | A3 | 3 |

### 根据时间要求选择

| 时间要求 | 推荐级别 | 预期时间 |
|----------|----------|----------|
| 快速验证 | A0 | 几分钟 |
| 标准测试 | A1 | 几小时 |
| 深度测试 | A2 | 几小时到一天 |
| 长期渗透 | A3 | 几天到几周 |

## ⚠️ 注意事项

### 1. 法律合规
- 确保在授权范围内使用
- 遵守相关法律法规
- 不要对未授权目标使用

### 2. 技术风险
- A0级别容易被检测
- A3级别速度较慢
- 根据实际情况调整

### 3. 资源管理
- 监控系统资源使用
- 避免过度消耗目标资源
- 合理设置线程数

---

**相关链接**: [快速开始](Getting-Started) | [配置说明](Configuration) | [使用教程](Tutorials) 