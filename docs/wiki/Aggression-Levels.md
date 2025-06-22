# 对抗级别详解

WebLoginBrute提供了4个预设的对抗级别，用于适应不同的安全环境和防护强度。

## A0 - 静默模式

**适用场景**: 测试环境、无防护目标、快速验证

**特点**:
- 最高速度，几乎没有延迟
- 适合在没有WAF/IPS的环境中快速测试
- 风险：容易被检测和封禁

**配置示例**:
```yaml
level: "A0"
```

**命令行使用**:
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --level A0
```

## A1 - 标准模式（默认）

**适用场景**: 一般网站、基础防护

**特点**:
- 适中的延迟和随机性
- 能规避基础的频率限制
- 平衡了速度和隐蔽性

**配置示例**:
```yaml
level: "A1"
```

**命令行使用**:
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --level A1
```

## A2 - 激进模式

**适用场景**: 中等安全防护、有WAF的目标

**特点**:
- 更长的延迟和更大的随机性
- 模拟耐心的攻击者行为
- 能规避大部分WAF检测

**配置示例**:
```yaml
level: "A2"
```

**命令行使用**:
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --level A2
```

## A3 - 极限模式

**适用场景**: 高安全目标、严格访问控制

**特点**:
- 非常长的延迟
- 最大程度的隐蔽性
- 用于对抗严格的行为分析

**配置示例**:
```yaml
level: "A3"
```

**命令行使用**:
```bash
python -m webloginbrute \
  --form https://example.com/login \
  --submit https://example.com/login \
  --users users.txt \
  --passwords passwords.txt \
  --level A3
```

## 级别对比

| 级别 | 延迟范围 | 随机性 | 速度 | 隐蔽性 | 适用场景 |
|------|----------|--------|------|--------|----------|
| A0 | 0-0.1s | 低 | 最快 | 低 | 测试环境 |
| A1 | 0.5-1s | 中 | 快 | 中 | 一般网站 |
| A2 | 1-3s | 高 | 中 | 高 | 有WAF |
| A3 | 2-5s | 最高 | 慢 | 最高 | 高安全 |

## 动态调整

你可以根据目标响应动态调整对抗级别：

```bash
# 开始时使用标准级别
level: "A1"

# 如果遇到频率限制，切换到更高级别
level: "A2"

# 对于高安全目标，直接使用极限级别
level: "A3"
```

## 最佳实践

1. **从标准级别开始**: 大多数情况下，A1级别已经足够
2. **根据响应调整**: 如果遇到频率限制，升级到A2或A3
3. **考虑目标环境**: 企业级目标通常需要A2或A3级别
4. **监控日志**: 观察是否触发安全防护，及时调整策略

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
level: "A0"

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
target_url: "https://test.example.com/login"
success_redirect: "https://test.example.com/dashboard"
failure_redirect: "https://test.example.com/login"
username_list: "users.txt"
password_list: "passwords.txt"
threads: 20
level: "A0"
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
level: "A1"

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
target_url: "https://example.com/login"
success_redirect: "https://example.com/dashboard"
failure_redirect: "https://example.com/login"
username_list: "users.txt"
password_list: "passwords.txt"
threads: 10
level: "A1"
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
level: "A2"

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
target_url: "https://secure.example.com/login"
success_redirect: "https://secure.example.com/dashboard"
failure_redirect: "https://secure.example.com/login"
username_list: "users.txt"
password_list: "passwords.txt"
threads: 5
level: "A2"
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
level: "A3"

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
target_url: "https://bank.example.com/login"
success_redirect: "https://bank.example.com/dashboard"
failure_redirect: "https://bank.example.com/login"
username_list: "users.txt"
password_list: "passwords.txt"
threads: 3
level: "A3"
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
level: "A0"
threads: 20

# 2. 如果被检测，升级到A1
level: "A1"
threads: 10

# 3. 如果仍有问题，升级到A2
level: "A2"
threads: 5

# 4. 最后使用A3
level: "A3"
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
level: "A2"
min_delay: 0.5      # 覆盖默认的1.0
max_delay: 3.0      # 覆盖默认的5.0
jitter_factor: 0.5  # 覆盖默认的0.3
```

### 混合策略

```yaml
# 使用A1级别但启用会话池
level: "A1"
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