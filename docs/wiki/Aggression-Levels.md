# 对抗级别详解

WebLoginBrute 提供了4个对抗级别，从0到3，每个级别都有不同的策略和参数配置。

## 级别概览

| 级别 | 名称 | 描述 | 适用场景 |
|------|------|------|----------|
| 0 | 静默模式 | 最低对抗，最快速度 | 测试环境、内部网络 |
| 1 | 标准模式 | 平衡性能和隐蔽性 | 一般Web应用 |
| 2 | 激进模式 | 高对抗，较慢速度 | 有WAF保护的目标 |
| 3 | 极限模式 | 最高对抗，最慢速度 | 高安全性目标 |

## 级别0 - 静默模式

### 配置示例

```yaml
aggressive: 0
```

### 特点

- **最快速度**: 无延迟，全速运行
- **最低隐蔽性**: 容易被检测
- **适合场景**: 测试环境、内部网络、无防护目标

### 参数配置

```yaml
# 静默模式配置
aggressive: 0
threads: 20
timeout: 10
max_retries: 1
base_delay: 0
session_lifetime: 600
max_session_pool_size: 200
enable_adaptive_rate_control: false
```

## 级别1 - 标准模式

### 配置示例

```yaml
aggressive: 1
```

### 特点

- **平衡性能**: 适中的速度和隐蔽性
- **智能重试**: 自动处理临时错误
- **适合场景**: 一般Web应用、生产环境

### 参数配置

```yaml
# 标准模式配置
aggressive: 1
threads: 10
timeout: 30
max_retries: 3
base_delay: 1.0
session_lifetime: 300
max_session_pool_size: 100
enable_adaptive_rate_control: true
```

## 级别2 - 激进模式

### 配置示例

```yaml
aggressive: 2
```

### 特点

- **高对抗性**: 更强的隐蔽能力
- **智能延迟**: 动态调整请求间隔
- **适合场景**: 有WAF保护的目标、高安全性环境

### 参数配置

```yaml
# 激进模式配置
aggressive: 2
threads: 5
timeout: 45
max_retries: 5
base_delay: 2.0
session_lifetime: 180
max_session_pool_size: 50
enable_adaptive_rate_control: true
rate_adjustment_threshold: 3
```

## 级别3 - 极限模式

### 配置示例

```yaml
aggressive: 3
```

### 特点

- **最高对抗**: 最强的隐蔽能力
- **极慢速度**: 非常保守的请求策略
- **适合场景**: 高安全性目标、有高级防护的目标

### 参数配置

```yaml
# 极限模式配置
aggressive: 3
threads: 2
timeout: 60
max_retries: 7
base_delay: 5.0
session_lifetime: 120
max_session_pool_size: 20
enable_adaptive_rate_control: true
rate_adjustment_threshold: 2
```

## 级别对比

| 参数 | 级别0 | 级别1 | 级别2 | 级别3 |
|------|-------|-------|-------|-------|
| 线程数 | 20 | 10 | 5 | 2 |
| 超时时间 | 10s | 30s | 45s | 60s |
| 重试次数 | 1 | 3 | 5 | 7 |
| 基础延迟 | 0s | 1s | 2s | 5s |
| 会话生命周期 | 600s | 300s | 180s | 120s |
| 会话池大小 | 200 | 100 | 50 | 20 |
| 自适应控制 | 关闭 | 开启 | 开启 | 开启 |

## 选择建议

### 测试环境
```yaml
aggressive: 0  # 全速测试
```

### 一般Web应用
```yaml
aggressive: 1  # 标准模式
```

### 有WAF保护
```yaml
aggressive: 2  # 激进模式
```

### 高安全性目标
```yaml
aggressive: 3  # 极限模式
```

## 动态调整

在运行过程中，可以根据目标响应动态调整对抗级别：

```bash
# 从标准模式开始
webloginbrute --config config.yaml -A 1

# 如果遇到频率限制，切换到激进模式
sed -i 's/aggressive: 1/aggressive: 2/' config.yaml
webloginbrute --config config.yaml --resume
```

## 最佳实践

1. **从低级别开始**: 建议从级别1开始，根据情况调整
2. **监控响应**: 注意观察目标的响应模式
3. **适时调整**: 遇到防护时及时提高级别
4. **平衡考虑**: 在速度和隐蔽性之间找到平衡

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