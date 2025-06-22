# 常见问题 (FAQ)

**WebLoginBrute v0.0.14** 常见问题解答

## 🔧 基础问题

### Q: 如何配置CSRF token字段？
A: 使用 `--csrf` 参数指定CSRF token字段名，例如：
```bash
--csrf "_token"
--csrf "csrf_token"
--csrf "authenticity_token"
```

### Q: 目标网站没有CSRF token怎么办？
A: 如果目标网站没有CSRF保护，可以完全省略 `--csrf` 参数：
```bash
python3 webloginbrute.py \
  --form-url "https://target.com/login" \
  --submit-url "https://target.com/login" \
  --username-file users.txt \
  --password-file passwords.txt
```

### Q: 如何找到CSRF token字段名？
A: 可以通过以下方法：
1. 查看登录页面源代码，寻找 `<input type="hidden" name="...">` 标签
2. 使用浏览器开发者工具检查表单字段
3. 查看网络请求中的表单数据

### Q: 提示"缺少CSRF token"错误怎么办？
A: 这个错误通常出现在以下情况：
1. **目标确实有CSRF保护**：请提供正确的 `--csrf` 参数
2. **目标没有CSRF保护**：可以省略 `--csrf` 参数
3. **Token字段名错误**：请检查并修正字段名

## 🚀 运行问题

### Q: 程序运行很慢怎么办？
A: 可以尝试以下优化：
1. 增加并发线程数：`--threads 10`
2. 降低对抗级别：`--aggression-level A0`
3. 减少超时时间：`--timeout 15`
4. 使用更快的网络连接

### Q: 遇到频率限制怎么办？
A: 程序会自动检测和处理频率限制，也可以：
1. 降低对抗级别：`--aggression-level A2` 或 `A3`
2. 减少并发数：`--threads 2`
3. 增加延迟时间
4. 使用代理轮换

### Q: 程序中断后如何继续？
A: 使用 `--resume` 参数可以从上次中断的地方继续：
```bash
python3 webloginbrute.py \
  --form-url "https://target.com/login" \
  --submit-url "https://target.com/login" \
  --username-file users.txt \
  --password-file passwords.txt \
  --csrf "token" \
  --resume
```

### Q: 如何测试配置而不实际攻击？
A: 使用 `--dry-run` 参数进行测试：
```bash
python3 webloginbrute.py \
  --form-url "https://target.com/login" \
  --submit-url "https://target.com/login" \
  --username-file users.txt \
  --password-file passwords.txt \
  --csrf "token" \
  --dry-run \
  --verbose
```

## 📊 结果问题

### Q: 如何判断登录是否成功？
A: 程序会通过以下方式判断：
1. HTTP状态码检查
2. 响应内容关键词分析
3. 重定向URL检查
4. 成功/失败关键词匹配

### Q: 没有找到有效凭据怎么办？
A: 可能的原因：
1. 字典文件不包含正确的凭据
2. 目标有额外的安全措施
3. 登录检测逻辑需要调整
4. 网络连接问题

### Q: 如何查看详细的运行日志？
A: 使用 `--verbose` 参数查看详细日志：
```bash
--verbose
```
日志文件保存在 `logs/` 目录下。

## 🔒 安全问题

### Q: 如何避免被目标检测？
A: 建议：
1. 使用合适的对抗级别
2. 控制请求频率
3. 使用代理轮换
4. 模拟真实用户行为
5. 避免在高峰时段攻击

### Q: 程序会留下痕迹吗？
A: 程序会：
1. 生成日志文件（可配置）
2. 保存进度文件（可清理）
3. 记录审计日志
4. 建议定期清理这些文件

### Q: 如何保护敏感信息？
A: 程序内置安全措施：
1. 日志脱敏处理
2. 敏感数据哈希化
3. 审计日志分离
4. 内存安全清理

## 🛠️ 技术问题

### Q: 支持哪些Python版本？
A: 支持Python 3.7及以上版本，推荐使用Python 3.8+。

### Q: 依赖包安装失败怎么办？
A: 常见解决方案：
1. 升级pip：`pip install --upgrade pip`
2. 使用虚拟环境
3. 检查Python版本兼容性
4. 手动安装依赖包

### Q: 内存使用过高怎么办？
A: 程序有自动内存管理，也可以：
1. 减少并发线程数
2. 使用更小的字典文件
3. 定期重启程序
4. 增加系统内存

### Q: 网络连接不稳定怎么办？
A: 建议：
1. 增加超时时间：`--timeout 60`
2. 使用重试机制
3. 检查网络稳定性
4. 使用代理服务器

## 📝 其他问题

### Q: 如何贡献代码？
A: 欢迎提交Pull Request：
1. Fork项目仓库
2. 创建功能分支
3. 提交代码更改
4. 创建Pull Request

### Q: 如何报告Bug？
A: 请在GitHub Issues中报告：
1. 详细描述问题
2. 提供错误日志
3. 说明复现步骤
4. 提供环境信息

### Q: 如何获取最新版本？
A: 可以通过以下方式：
1. 从GitHub下载最新发布版
2. 使用git克隆仓库
3. 关注项目更新通知

### Q: 有商业支持吗？
A: 目前提供社区支持，如有商业需求请联系项目维护者。

---

**相关链接**: [安装指南](Installation) | [快速开始](Getting-Started) | [配置说明](Configuration) | [故障排除](Troubleshooting) 

# FAQ - 常见问题解答

**版本：0.0.27**

## Q1: 为什么我的爆破速度很慢？
A: 可能是以下原因之一：
1.  **对抗级别过高**: `A2` 或 `A3` 级别会引入大量延迟以规避检测。尝试降低到 `A1` 或 `A0`。
2.  **网络延迟**: 目标服务器响应慢或你的网络环境不佳。
3.  **并发线程数过低**: 尝试在 `--threads` 或 `config.yaml` 中适当增加并发数。

## Q2: 程序提示"配置参数校验失败"，我该怎么办？
A: 这意味着你的配置项不符合要求。请检查：
1.  **必需项是否都已提供**: `form`, `submit`, `users`, `passwords`。
2.  **文件路径是否正确**: 字典文件、cookie文件等是否存在。
3.  **参数类型是否正确**: `threads` 和 `timeout` 必须是整数。
4.  **URL格式是否正确**: 必须以 `http://` 或 `https://` 开头。

## Q3: 为什么爆破结果显示"0次成功"，但日志里有很多错误？
A: 请检查日志中的错误类型：
- **`RateLimitError`**: 目标可能已触发频率限制，建议提高对抗级别或降低并发数。
- **`CaptchaDetected`**: 目标已出现验证码，该工具无法自动处理，建议更换代理IP或等待后重试。
- **`ConnectionError` / `Timeout`**: 网络问题或目标不稳定，建议增加 `--timeout` 值。

## Q4: 我可以在代码中直接使用WebLoginBrute吗？
A: 可以。请参考 [API参考 & 开发者指南](API-Reference.md) 中的示例，你可以通过编程方式创建 `Config` 对象并调用 `WebLoginBrute` 类。

## Q5: 这个工具能绕过所有WAF吗？
A: **不能**。该工具的对抗级别和动态延迟能规避一些基础的WAF策略，但无法保证绕过所有高级WAF。 