# 快速开始

**WebLoginBrute v0.0.14** - 企业级Web登录暴力破解工具

## 🚀 安装

## 🚀 基础使用

### 1. 基本命令格式

```bash
python3 webloginbrute.py --form-url <表单URL> --submit-url <提交URL> --username-file <用户名字典> --password-file <密码字典>
```

### 2. 完整示例

#### 有CSRF Token的目标
```bash
python3 webloginbrute.py \
  --form-url "https://example.com/login" \
  --submit-url "https://example.com/login" \
  --username-file users.txt \
  --password-file passwords.txt \
  --csrf "_token" \
  --threads 5 \
  --timeout 30
```

#### 无CSRF Token的目标
```bash
python3 webloginbrute.py \
  --form-url "https://example.com/login" \
  --submit-url "https://example.com/login" \
  --username-file users.txt \
  --password-file passwords.txt \
  --threads 5 \
  --timeout 30
```

**注意**：如果目标网站没有CSRF token保护，可以省略 `--csrf` 参数。

### 3. 参数说明

#### 必需参数
- `--form-url`: 登录表单页面URL
- `--submit-url`: 登录提交URL
- `--username-file`: 用户名字典文件路径
- `--password-file`: 密码字典文件路径

#### 可选参数
- `--csrf`: CSRF token字段名（如目标无CSRF token可省略）
- `--login-field`: 额外的登录字段名
- `--login-value`: 额外的登录字段值
- `--cookie-file`: Cookie文件路径
- `--timeout`: 请求超时时间（秒，默认30）
- `--threads`: 并发线程数（默认5）
- `--resume`: 从上次中断的地方继续
- `--aggression-level`: 对抗级别（A0-A3，默认A1）
- `--dry-run`: 测试模式，不实际发送请求
- `--verbose`: 详细输出

## 📋 使用场景

### 场景1：标准Web应用登录
```bash
python3 webloginbrute.py \
  --form-url "https://target.com/login" \
  --submit-url "https://target.com/login" \
  --username-file users.txt \
  --password-file passwords.txt \
  --csrf "csrf_token"
```

### 场景2：无CSRF保护的简单登录
```bash
python3 webloginbrute.py \
  --form-url "https://target.com/login" \
  --submit-url "https://target.com/login" \
  --username-file users.txt \
  --password-file passwords.txt
```

### 场景3：需要额外字段的登录
```bash
python3 webloginbrute.py \
  --form-url "https://target.com/login" \
  --submit-url "https://target.com/login" \
  --username-file users.txt \
  --password-file passwords.txt \
  --csrf "token" \
  --login-field "remember" \
  --login-value "1"
```

### 场景4：高对抗级别攻击
```bash
python3 webloginbrute.py \
  --form-url "https://target.com/login" \
  --submit-url "https://target.com/login" \
  --username-file users.txt \
  --password-file passwords.txt \
  --csrf "csrf_token" \
  --aggression-level A3 \
  --threads 2 \
  --timeout 60
```

## 🔧 高级配置

### 对抗级别说明
- **A0 (静默模式)**: 最低对抗，适合测试环境
- **A1 (标准模式)**: 默认级别，平衡性能和稳定性
- **A2 (激进模式)**: 高对抗，适合有防护的目标
- **A3 (极限模式)**: 最高对抗，适合强防护目标

### 会话恢复
```bash
# 中断后继续
python3 webloginbrute.py \
  --form-url "https://target.com/login" \
  --submit-url "https://target.com/login" \
  --username-file users.txt \
  --password-file passwords.txt \
  --csrf "token" \
  --resume
```

### 测试模式
```bash
# 测试配置而不实际攻击
python3 webloginbrute.py \
  --form-url "https://target.com/login" \
  --submit-url "https://target.com/login" \
  --username-file users.txt \
  --password-file passwords.txt \
  --csrf "token" \
  --dry-run \
  --verbose
```

## 📊 输出说明

### 实时输出
```
2024-01-15 10:30:15 - INFO - WebLoginBrute v0.0.14 启动
2024-01-15 10:30:15 - INFO - 加载了 100 个用户名和 1000 个密码
2024-01-15 10:30:15 - INFO - 开始暴力破解，总共 100000 个组合
```

### 最终统计
```
==================================================
暴力破解完成
==================================================
总尝试次数: 1500
成功次数: 1
超时错误: 0
连接错误: 0
HTTP错误: 0
其他错误: 0
重试次数: 0
频率限制: 0
验证码检测: 0
总耗时: 45.23 秒
平均响应时间: 0.030 秒
峰值内存使用: 45.2 MB
内存清理次数: 2
==================================================
```

## ⚠️ 注意事项

1. **合法使用**: 仅用于授权的安全测试
2. **频率控制**: 避免对目标造成过大压力
3. **日志管理**: 定期清理日志文件
4. **资源监控**: 注意内存和CPU使用情况
5. **网络稳定**: 确保网络连接稳定

## 🆘 常见问题

### Q: 提示"缺少CSRF token"怎么办？
A: 如果目标网站没有CSRF保护，可以省略 `--csrf` 参数。

### Q: 如何提高成功率？
A: 可以尝试调整对抗级别、减少并发数、增加超时时间。

### Q: 程序中断后如何继续？
A: 使用 `--resume` 参数可以从上次中断的地方继续。

### Q: 如何查看详细日志？
A: 使用 `--verbose` 参数可以查看DEBUG级别的详细日志。 