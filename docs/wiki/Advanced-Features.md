# 高级特性

## 🔒 企业级安全防护

### XXE防护
WebLoginBrute 使用安全的HTML解析器，防止XML外部实体（XXE）攻击：

```python
# 使用安全的html.parser替代lxml
soup = BeautifulSoup(html, 'html.parser')
```

**安全优势**：
- 防止恶意XML实体攻击
- 避免外部文件读取
- 提高解析安全性

### 路径遍历防护
全面的路径安全检查，防止目录遍历攻击：

```python
# 路径遍历检测
path_traversal_patterns = [
    r'\.\./', r'\.\.\\', r'\.\.\\\\',
    r'\.\.\.', r'\.\.\.\.',
    r'\.\.',  # 检测单独的..
]
```

**防护机制**：
- 检测常见的路径遍历模式
- 验证路径规范化
- 检查符号链接
- 限制绝对路径访问

### 命令注入防护
输入验证和清理，防止命令注入攻击：

```python
# 命令注入检测
command_injection_patterns = [
    r'[;&|`$]\s*[a-zA-Z]',  # 命令分隔符后跟字母
]
```

**安全措施**：
- 检测命令分隔符
- 验证输入格式
- 清理危险字符

### SSRF防护
URL验证和重定向限制，防止服务器端请求伪造：

```python
# URL安全性验证
def validate_url(url, allow_private_networks=False):
    # 检查协议
    # 验证域名
    # 检查内网地址
    # 验证端口号
```

**防护特性**：
- 协议白名单验证
- 域名安全检查
- 内网地址控制
- 重定向URL验证

### ReDoS防护
安全的正则表达式使用，防止正则表达式拒绝服务攻击：

```python
# 使用简单模式替代复杂正则
# 避免嵌套和重复模式
# 限制匹配复杂度
```

**安全策略**：
- 避免复杂的嵌套模式
- 使用固定长度匹配
- 限制正则表达式复杂度

### 内存攻击防护
文件大小限制和JSON解析超时保护：

```python
# 文件大小限制
max_size = 100 * 1024 * 1024  # 100MB

# JSON解析超时
parse_thread.join(timeout=5)
```

**防护机制**：
- 文件大小限制
- JSON解析超时
- 内存使用监控
- 垃圾回收优化

## 🚀 智能对抗机制

### 四级对抗模式

#### A0 - 全速爆破模式
```bash
--aggression-level A0
```
**特点**：
- 无延迟和对抗机制
- 最大并发性能
- 适合低安全目标

#### A1 - 低对抗模式
```bash
--aggression-level A1
```
**特点**：
- 基础延迟（0.5-2秒）
- 简单防护检测
- 适合简单防护目标

#### A2 - 中对抗模式
```bash
--aggression-level A2
```
**特点**：
- 标准延迟（1-5秒）
- 完整防护检测
- 会话池管理
- 适合中等安全目标

#### A3 - 高对抗模式
```bash
--aggression-level A3
```
**特点**：
- 高级延迟（2-10秒）
- 完整仿真机制
- 高级会话管理
- 适合高安全目标

### 自适应速率控制
根据目标响应自动调整请求速率：

```python
# 自适应速率控制
self.adaptive_rate_stats = {
    'consecutive_errors': 0,
    'consecutive_successes': 0,
    'current_rate_multiplier': 1.0,
    'min_rate_multiplier': 0.1,
    'max_rate_multiplier': 2.0,
}
```

**控制策略**：
- 连续错误时降低速率
- 连续成功时提高速率
- 检测到429状态码立即降速
- 动态调整延迟时间

## 📊 性能监控

### 内存管理
智能内存清理和缓存机制：

```python
# 内存清理
def _cleanup_memory(self):
    # 清理DNS缓存
    # 清理过期会话
    # 清理频率限制记录
    # 强制垃圾回收
```

**优化特性**：
- 定期内存清理
- 缓存大小限制
- 会话生命周期管理
- 垃圾回收优化

### 性能统计
详细的性能指标监控：

```python
# 性能指标
self.performance = {
    'peak_memory_usage': 0,
    'avg_response_time': 0,
    'total_response_time': 0,
    'response_count': 0,
    'memory_cleanup_count': 0
}
```

**监控指标**：
- 峰值内存使用
- 平均响应时间
- 内存清理次数
- 响应成功率

## 🔐 会话管理

### 线程安全会话池
```python
# 会话池管理
self.session_pool = {}
self.session_pool_lock = Lock()
self.max_session_pool_size = 100
self.session_lifetime = 300
```

**管理特性**：
- 线程安全的会话池
- 会话生命周期管理
- 自动清理过期会话
- 会话池大小限制

### 会话恢复机制
智能会话恢复和验证：

```python
# 会话恢复
def check_resumed_session(self):
    # 加载保存的Cookie
    # 验证会话有效性
    # 检查登录状态
```

**恢复功能**：
- Cookie会话保存
- 会话有效性验证
- 自动会话恢复
- 会话状态检查

## 📝 审计日志

### 安全审计
独立的安全审计日志系统：

```python
# 审计日志
audit_logger = logging.getLogger('audit')
audit_logger.info(f"SECURITY_EVENT: {event_type} - {details}")
```

**审计功能**：
- 独立审计日志
- 安全事件记录
- 敏感信息脱敏
- SIEM集成支持

### 日志脱敏
敏感信息自动脱敏处理：

```python
# 日志脱敏
def _sanitize_log_message(self, message):
    patterns = [
        (r'username[:\s]*([^\s,]+)', r'username: ***'),
        (r'password[:\s]*([^\s,]+)', r'password: ***'),
    ]
```

**脱敏特性**：
- 用户名密码脱敏
- 敏感字段隐藏
- 响应内容清理
- 审计数据保护

## 🌐 网络优化

### DNS缓存
避免重复DNS解析：

```python
# DNS缓存
self._dns_cache = {}
self._dns_cache_lock = Lock()

def _resolve_host(self, host: str, timeout: float = 5.0):
    # 检查缓存
    # 解析域名
    # 缓存结果
```

**优化特性**：
- DNS结果缓存
- 解析超时控制
- 缓存大小限制
- 线程安全访问

### 智能重试
指数退避重试机制：

```python
# 重试机制
def _retry_with_backoff(self, func, *args, **kwargs):
    for attempt in range(self.max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            delay = self.base_delay * (2 ** attempt)
            time.sleep(delay)
```

**重试策略**：
- 指数退避延迟
- 最大重试次数限制
- 异常类型分类
- 智能错误处理

## 🔧 配置管理

### 配置文件验证
严格的配置文件验证：

```python
# 配置验证
def validate_basic_config(args):
    # 验证URL格式
    # 检查文件存在性
    # 验证参数范围
    # 安全检查配置
```

**验证功能**：
- 参数类型检查
- 值范围验证
- 文件路径安全
- 配置一致性检查

### 配置偏好保存
用户配置偏好管理：

```python
# 配置偏好
def save_config_preferences(self):
    config_data = {
        'timestamp': datetime.now().isoformat(),
        'version': __version__,
        'preferences': {...}
    }
```

**管理特性**：
- 配置偏好保存
- 版本兼容性
- 配置恢复
- 用户设置管理

## 🛡️ IP安全控制

### 白名单/黑名单
支持CIDR格式的IP控制：

```bash
# IP白名单
--ip-whitelist "192.168.1.0/24" "10.0.0.1"

# IP黑名单
--ip-blacklist "192.168.1.100" "10.0.0.0/8"
```

**控制特性**：
- CIDR格式支持
- 精确IP匹配
- 域名解析支持
- 动态IP检查

### 文件支持
从文件加载IP列表：

```bash
# 从文件加载
--ip-whitelist-file whitelist.txt
--ip-blacklist-file blacklist.txt
```

**文件格式**：
- 每行一个IP或CIDR
- 支持注释行（#开头）
- 自动域名解析
- 格式验证

## 📈 统计信息

### 详细统计
全面的尝试统计和错误分类：

```python
# 统计信息
self.stats = {
    'total_attempts': 0,
    'successful_attempts': 0,
    'timeout_errors': 0,
    'connection_errors': 0,
    'http_errors': 0,
    'other_errors': 0,
    'retry_attempts': 0,
    'rate_limited': 0,
    'captcha_detected': 0
}
```

**统计功能**：
- 尝试次数统计
- 错误类型分类
- 成功率计算
- 性能指标统计

### 实时监控
实时性能监控和报告：

```python
# 性能监控
def print_stats(self):
    # 计算成功率
    # 显示性能指标
    # 输出统计报告
    # 记录性能摘要
```

**监控特性**：
- 实时统计更新
- 性能指标显示
- 内存使用监控
- 响应时间统计

---

**⚠️ 重要提醒**: 请确保在授权范围内使用本工具，遵守相关法律法规。 