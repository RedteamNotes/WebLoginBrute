# 安装指南

## 📋 系统要求

### 基础要求
- **Python版本**: 3.7 或更高版本
- **操作系统**: Windows, macOS, Linux
- **内存**: 建议 2GB 以上
- **网络**: 稳定的网络连接

### 推荐配置
- **Python版本**: 3.8+
- **内存**: 4GB 以上
- **CPU**: 多核处理器
- **存储**: 至少 1GB 可用空间

## 🚀 安装步骤

### 1. 克隆项目
```bash
git clone https://github.com/RedteamNotes/WebLoginBrute.git
cd WebLoginBrute
```

### 2. 创建虚拟环境（推荐）
```bash
# 使用 venv (Python 3.3+)
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 验证安装
```bash
python webloginbrute.py --help
```

## 📦 依赖包说明

### 必需依赖
```
requests>=2.25.1          # HTTP请求库
beautifulsoup4>=4.9.3     # HTML解析库（使用安全的html.parser）
pyyaml>=5.4.1             # YAML配置文件支持
```

### 可选依赖
```
psutil>=5.8.0             # 性能监控（可选）
```

### 依赖包功能说明

#### requests
- **用途**: HTTP请求处理
- **版本要求**: 2.25.1+
- **功能**: 支持代理、会话管理、重试机制

#### beautifulsoup4
- **用途**: HTML解析
- **版本要求**: 4.9.3+
- **安全特性**: 使用 `html.parser` 而非 `lxml`，防止XXE攻击
- **功能**: 安全的HTML解析和元素提取

#### pyyaml
- **用途**: YAML配置文件支持
- **版本要求**: 5.4.1+
- **功能**: 安全的YAML配置加载和验证

#### psutil (可选)
- **用途**: 系统性能监控
- **版本要求**: 5.8.0+
- **功能**: 内存使用监控、性能统计

## 🔧 平台特定安装

### Windows 安装

#### 使用 pip
```bash
pip install requests beautifulsoup4 pyyaml psutil
```

#### 使用 conda
```bash
conda install requests beautifulsoup4 pyyaml psutil
```

### macOS 安装

#### 使用 Homebrew + pip
```bash
brew install python3
pip3 install requests beautifulsoup4 pyyaml psutil
```

#### 使用 conda
```bash
conda install requests beautifulsoup4 pyyaml psutil
```

### Linux 安装

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
pip3 install requests beautifulsoup4 pyyaml psutil
```

#### CentOS/RHEL
```bash
sudo yum install python3 python3-pip
pip3 install requests beautifulsoup4 pyyaml psutil
```

#### Arch Linux
```bash
sudo pacman -S python python-pip
pip install requests beautifulsoup4 pyyaml psutil
```

## 🛠️ 配置验证

### 1. 基础功能测试
```bash
python webloginbrute.py --validate-config
```

### 2. 依赖检查
```python
import requests
import yaml
from bs4 import BeautifulSoup
import psutil

print("所有依赖包安装成功！")
```

### 3. 安全功能测试
```bash
# 测试路径安全检查
python webloginbrute.py --form-url "http://test.com" --submit-url "http://test.com" --csrf "test" --fail-string "test" --users "test.txt" --passwords "test.txt" --dry-run
```

## 🔒 安全配置

### 1. 文件权限设置
```bash
# Linux/macOS
chmod 600 config.yaml
chmod 600 *.cookies
chmod 600 *.log
```

### 2. 防火墙配置
确保防火墙允许必要的网络连接：
- HTTP (80)
- HTTPS (443)
- 自定义代理端口

### 3. 代理设置（可选）
```bash
# 设置代理环境变量
export HTTP_PROXY="http://proxy:port"
export HTTPS_PROXY="http://proxy:port"
```

## 🚨 故障排除

### 常见安装问题

#### 1. Python版本问题
```bash
# 检查Python版本
python --version
python3 --version

# 如果版本过低，升级Python
```

#### 2. pip安装失败
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### 3. 权限问题
```bash
# 使用用户安装
pip install --user -r requirements.txt

# 或使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

#### 4. 依赖冲突
```bash
# 清理pip缓存
pip cache purge

# 重新安装
pip uninstall requests beautifulsoup4 pyyaml psutil
pip install -r requirements.txt
```

### 平台特定问题

#### Windows
- 确保安装了Visual C++ Build Tools
- 使用管理员权限运行命令提示符

#### macOS
- 确保安装了Xcode Command Line Tools
- 使用Homebrew管理Python版本

#### Linux
- 确保安装了python3-dev包
- 检查系统防火墙设置

## 📊 性能优化

### 1. 内存优化
- 使用虚拟环境隔离依赖
- 定期清理临时文件
- 监控内存使用情况

### 2. 网络优化
- 配置合适的超时时间
- 使用代理服务器
- 启用DNS缓存

### 3. 并发优化
- 根据系统性能调整线程数
- 启用自适应速率控制
- 监控CPU使用率

## 🔍 验证清单

安装完成后，请确认以下项目：

- [ ] Python 3.7+ 已安装
- [ ] 所有依赖包已安装
- [ ] 虚拟环境已创建（推荐）
- [ ] 文件权限已正确设置
- [ ] 网络连接正常
- [ ] 代理配置正确（如使用）
- [ ] 基础功能测试通过
- [ ] 安全配置已应用

## 📞 获取帮助

如果遇到安装问题，请：

1. 检查系统要求是否满足
2. 查看故障排除部分
3. 搜索GitHub Issues
4. 提交新的Issue

---

**⚠️ 重要提醒**: 请确保在授权范围内使用本工具，遵守相关法律法规。 