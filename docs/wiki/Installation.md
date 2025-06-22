# 安装指南

## 🚀 系统要求

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

## 🛠️ 安装步骤

### 1. 克隆项目
```bash
git clone https://github.com/RedteamNotes/WebLoginBrute.git
cd WebLoginBrute
```

### 2. 创建虚拟环境 (推荐)
```bash
# 使用 venv (Python 3.3+)
python -m venv venv
```

### 3. 激活虚拟环境
- **Windows**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

### 4. 安装依赖
```bash
pip install -r requirements.txt
```

### 5. 验证安装
运行以下命令，如果能看到帮助信息，则说明安装成功：
```bash
python -m webloginbrute --help
```

## 📦 依赖包说明

本项目依赖以下核心 Python 包：

- **requests**: 用于发送 HTTP 请求。
- **beautifulsoup4**: 用于解析 HTML 内容。
- **PyYAML**: 用于解析 YAML 配置文件。
- **psutil**: 用于获取系统性能信息。
- **pydantic**: 用于数据验证和配置管理。
- **chardet**: 用于自动检测字典文件编码。

所有依赖及其版本都已在 `requirements.txt` 文件中详细列出。

## 🚨 故障排除

### 1. pip 安装失败
如果 `pip install` 命令失败或速度过慢，可以尝试使用国内的 PyPI 镜像源：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 2. Python 版本问题
请确保您的 `python` 命令指向的是 3.7 或更高版本的解释器。您可以通过以下命令检查：
```bash
python --version
```
如果您的系统默认 Python 是 2.x 版本，请尝试使用 `python3` 命令。
```bash
python3 -m venv venv
python3 -m pip install -r requirements.txt
python3 -m webloginbrute --help
```

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