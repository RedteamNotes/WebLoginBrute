# API参考

本文档提供了WebLoginBrute的完整API参考，包含类、方法和参数的详细说明。

## 📋 目录

- [WebLoginBrute类](#webloginbrute类)
- [配置类](#配置类)
- [方法参考](#方法参考)
- [常量定义](#常量定义)
- [异常处理](#异常处理)

## 🔧 WebLoginBrute类

### 类定义

```python
class WebLoginBrute:
    """
    CSRF登录暴力破解工具主类
    
    提供智能的会话管理、动态CSRF Token刷新和四级对抗策略
    """
```

### 构造函数

```python
def __init__(self, config):
    """
    初始化WebLoginBrute实例
    
    Args:
        config: 配置对象或字典，包含所有必要的参数
    
    Raises:
        ValueError: 配置参数无效
        FileNotFoundError: 字典文件不存在
    """
```

### 主要属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `config` | Config | 配置对象 |
| `success` | bool | 是否已找到有效凭据 |
| `lock` | RLock | 线程锁 |
| `executor` | ThreadPoolExecutor | 线程池执行器 |
| `stats` | dict | 统计信息 |
| `performance` | dict | 性能监控数据 |
| `session_pool` | dict | 会话池 |
| `aggression_level` | str | 对抗级别 |

## ⚙️ 配置类

### 配置参数

```python
class Config:
    """配置类，包含所有配置参数"""
    
    # 目标配置
    target_url: str              # 登录页面URL
    success_redirect: str        # 成功重定向URL
    failure_redirect: str        # 失败重定向URL
    
    # 字典配置
    username_list: str           # 用户名列表文件
    password_list: str           # 密码列表文件
    
    # 线程配置
    threads: int                 # 并发线程数
    
    # 代理配置
    proxy: Optional[str]         # 代理服务器地址
    
    # 对抗级别配置
    aggression_level: str        # 对抗级别 (A0/A1/A2/A3)
    
    # 延迟配置
    min_delay: float            # 最小延迟时间
    max_delay: float            # 最大延迟时间
    jitter_factor: float        # 抖动因子
    
    # 智能延迟配置
    enable_smart_delay: bool    # 启用智能延迟
    enable_session_pool: bool   # 启用会话池
    session_lifetime: int       # 会话生命周期
    
    # 防护检测配置
    enable_rate_limit_detection: bool  # 启用频率限制检测
    enable_captcha_detection: bool     # 启用验证码检测
    
    # 进度保存配置
    progress_file: str          # 进度保存文件
    
    # 日志配置
    log_level: str              # 日志级别
    log_file: str               # 日志文件路径
```

## 🔧 方法参考

### 核心方法

#### run()

```python
def run(self):
    """
    执行CSRF爆破任务
    
    这是主要的执行方法，会：
    1. 初始化线程池
    2. 加载字典文件
    3. 执行爆破任务
    4. 显示统计信息
    
    Returns:
        bool: 是否找到有效凭据
    """
```

#### worker()

```python
def worker(self, username: str, password: str):
    """
    为每个密码组合执行登录尝试
    
    Args:
        username (str): 用户名
        password (str): 密码
    
    这个方法会：
    1. 获取登录页面和CSRF Token
    2. 执行登录请求
    3. 检查登录结果
    4. 处理各种异常情况
    """
```

### 配置方法

#### _setup_aggression_level()

```python
def _setup_aggression_level(self):
    """
    根据对抗级别设置相应的参数
    
    支持的对抗级别：
    - A0: 全速爆破模式
    - A1: 低对抗模式
    - A2: 中对抗模式
    - A3: 高对抗模式
    """
```

### 会话管理方法

#### _get_session_for_user()

```python
def _get_session_for_user(self, username: str) -> requests.Session:
    """
    为用户获取或创建会话
    
    Args:
        username (str): 用户名
    
    Returns:
        requests.Session: 会话对象
    
    根据对抗级别：
    - A0: 每次都创建新会话
    - A1-A3: 使用会话池管理
    """
```

#### _get_smart_delay()

```python
def _get_smart_delay(self) -> float:
    """
    获取智能延迟时间
    
    Returns:
        float: 延迟时间（秒）
    
    根据对抗级别返回不同的延迟：
    - A0: 0.0-0.1秒
    - A1: 0.5-2.0秒
    - A2: 1.0-5.0秒
    - A3: 2.0-10.0秒
    """
```

### 检测方法

#### _detect_rate_limiting()

```python
def _detect_rate_limiting(self, response: requests.Response) -> bool:
    """
    检测频率限制
    
    Args:
        response (requests.Response): HTTP响应对象
    
    Returns:
        bool: 是否检测到频率限制
    
    检测指标：
    - HTTP状态码429
    - 响应内容包含频率限制关键词
    """
```

#### _detect_captcha()

```python
def _detect_captcha(self, response: requests.Response) -> bool:
    """
    检测验证码
    
    Args:
        response (requests.Response): HTTP响应对象
    
    Returns:
        bool: 是否检测到验证码
    
    检测指标：
    - 响应内容包含验证码关键词
    - HTML结构包含验证码元素
    """
```

### 处理方法

#### _handle_rate_limiting()

```python
def _handle_rate_limiting(self, username: str, password: str):
    """
    处理频率限制
    
    Args:
        username (str): 用户名
        password (str): 密码
    
    处理策略：
    - 记录到统计信息
    - 根据对抗级别等待不同时间
    - 清理相关会话
    """
```

#### _handle_captcha()

```python
def _handle_captcha(self, username: str, password: str):
    """
    处理验证码
    
    Args:
        username (str): 用户名
        password (str): 密码
    
    处理策略：
    - 记录到统计信息
    - 根据对抗级别等待不同时间
    - 清理相关会话
    """
```

### 工具方法

#### _get_login_page()

```python
def _get_login_page(self, session: requests.Session, 
                   username: str, password: str) -> Tuple[requests.Response, str]:
    """
    获取登录页面和CSRF Token
    
    Args:
        session (requests.Session): 会话对象
        username (str): 用户名
        password (str): 密码
    
    Returns:
        Tuple[requests.Response, str]: (响应对象, CSRF Token)
    
    Raises:
        requests.RequestException: 网络请求异常
        ValueError: Token获取失败
    """
```

#### _prepare_login_data()

```python
def _prepare_login_data(self, username: str, password: str, 
                       token: str) -> dict:
    """
    准备登录数据
    
    Args:
        username (str): 用户名
        password (str): 密码
        token (str): CSRF Token
    
    Returns:
        dict: 登录表单数据
    """
```

#### _perform_login()

```python
def _perform_login(self, session: requests.Session, 
                  data: dict, headers: dict) -> requests.Response:
    """
    执行登录请求
    
    Args:
        session (requests.Session): 会话对象
        data (dict): 登录数据
        headers (dict): 请求头
    
    Returns:
        requests.Response: 登录响应
    
    Raises:
        requests.RequestException: 网络请求异常
    """
```

#### _check_login_result()

```python
def _check_login_result(self, username: str, password: str, 
                       response: requests.Response, 
                       session: requests.Session):
    """
    检查登录结果
    
    Args:
        username (str): 用户名
        password (str): 密码
        response (requests.Response): 登录响应
        session (requests.Session): 会话对象
    
    检查逻辑：
    - 比较重定向URL
    - 检查响应内容
    - 更新统计信息
    """
```

### 统计方法

#### update_stats()

```python
def update_stats(self, stat_type: str):
    """
    更新统计信息
    
    Args:
        stat_type (str): 统计类型
    
    支持的统计类型：
    - 'total_attempts': 总尝试次数
    - 'successful_attempts': 成功次数
    - 'timeout_errors': 超时错误
    - 'connection_errors': 连接错误
    - 'http_errors': HTTP错误
    - 'other_errors': 其他错误
    - 'rate_limited': 频率限制
    - 'captcha_detected': 验证码检测
    """
```

#### print_stats()

```python
def print_stats(self):
    """
    打印统计信息
    
    显示内容：
    - 对抗级别
    - 总尝试次数
    - 成功次数
    - 各种错误统计
    - 性能指标
    - 反机器人统计
    """
```

### 文件操作方法

#### save_progress()

```python
def save_progress(self, username: str, password: str):
    """
    保存进度
    
    Args:
        username (str): 当前用户名
        password (str): 当前密码
    
    保存内容：
    - 已尝试的组合
    - 统计信息
    - 性能数据
    """
```

#### load_progress()

```python
def load_progress(self) -> bool:
    """
    加载进度
    
    Returns:
        bool: 是否成功加载进度
    
    加载内容：
    - 已尝试的组合
    - 统计信息
    - 性能数据
    """
```

## 📊 常量定义

### 对抗级别配置

```python
AGGRESSION_CONFIGS = {
    'A0': {  # 全速爆破
        'min_delay': 0.0,
        'max_delay': 0.1,
        'jitter_factor': 0.0,
        'enable_smart_delay': False,
        'enable_session_pool': False,
        'enable_rate_limit_detection': False,
        'enable_captcha_detection': False,
        'session_lifetime': 0,
        'description': '全速爆破模式 - 无任何延迟和对抗机制'
    },
    'A1': {  # 低对抗
        'min_delay': 0.5,
        'max_delay': 2.0,
        'jitter_factor': 0.2,
        'enable_smart_delay': True,
        'enable_session_pool': False,
        'enable_rate_limit_detection': True,
        'enable_captcha_detection': True,
        'session_lifetime': 60,
        'description': '低对抗模式 - 基础延迟和检测，适合简单防护目标'
    },
    'A2': {  # 中对抗
        'min_delay': 1.0,
        'max_delay': 5.0,
        'jitter_factor': 0.3,
        'enable_smart_delay': True,
        'enable_session_pool': True,
        'enable_rate_limit_detection': True,
        'enable_captcha_detection': True,
        'session_lifetime': 300,
        'description': '中对抗模式 - 标准仿真和防护，适合中等安全目标'
    },
    'A3': {  # 高对抗
        'min_delay': 2.0,
        'max_delay': 10.0,
        'jitter_factor': 0.5,
        'enable_smart_delay': True,
        'enable_session_pool': True,
        'enable_rate_limit_detection': True,
        'enable_captcha_detection': True,
        'session_lifetime': 600,
        'description': '高对抗模式 - 高级仿真和防护，适合高安全目标'
    }
}
```

### User-Agent列表

```python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
    # ... 更多User-Agent
]
```

### 浏览器头信息

```python
BROWSER_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}
```

## ⚠️ 异常处理

### 自定义异常

```python
class WebLoginBruteError(Exception):
    """WebLoginBrute基础异常类"""
    pass

class ConfigError(WebLoginBruteError):
    """配置错误异常"""
    pass

class TokenError(WebLoginBruteError):
    """Token获取失败异常"""
    pass

class LoginError(WebLoginBruteError):
    """登录失败异常"""
    pass
```

### 异常处理示例

```python
try:
    brute = WebLoginBrute(config)
    success = brute.run()
except ConfigError as e:
    print(f"配置错误: {e}")
except TokenError as e:
    print(f"Token获取失败: {e}")
except LoginError as e:
    print(f"登录失败: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 🔧 使用示例

### 基本使用

```python
from webloginbrute import WebLoginBrute
import yaml

# 加载配置
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# 创建实例
brute = WebLoginBrute(config)

# 执行爆破
success = brute.run()

# 打印统计
brute.print_stats()
```

### 高级使用

```python
from webloginbrute import WebLoginBrute
import yaml

# 自定义配置
config = {
    'target_url': 'https://example.com/login',
    'success_redirect': 'https://example.com/dashboard',
    'failure_redirect': 'https://example.com/login',
    'username_list': 'users.txt',
    'password_list': 'passwords.txt',
    'threads': 10,
    'aggression_level': 'A2',
    'proxy': 'http://127.0.0.1:8080'
}

# 创建实例
brute = WebLoginBrute(config)

# 执行爆破
try:
    success = brute.run()
    if success:
        print("找到有效凭据！")
    else:
        print("未找到有效凭据")
except Exception as e:
    print(f"执行失败: {e}")
finally:
    # 打印统计
    brute.print_stats()
```

### 集成使用

```python
from webloginbrute import WebLoginBrute
import yaml
import json

class SecurityTester:
    def __init__(self, config_file):
        with open(config_file) as f:
            self.config = yaml.safe_load(f)
    
    def run_csrf_test(self):
        """执行CSRF测试"""
        brute = WebLoginBrute(self.config)
        success = brute.run()
        
        # 保存结果
        results = {
            'success': success,
            'stats': brute.stats,
            'performance': brute.performance
        }
        
        with open('csrf_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        return results

# 使用
tester = SecurityTester('config.yaml')
results = tester.run_csrf_test()
```

---

**相关链接**: [快速开始](Getting-Started) | [配置说明](Configuration) | [使用教程](Tutorials) 