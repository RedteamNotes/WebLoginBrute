# 安装指南

## 🚀 系统要求

### 基础要求
- **Python 版本**: 3.8 或更高版本
- **操作系统**: Windows, macOS, Linux
- **内存**: 建议 2GB 以上
- **网络**: 稳定的网络连接

### 推荐配置
- **Python 版本**: 3.9+
- **内存**: 4GB 以上
- **CPU**: 多核处理器

## 🛠️ 安装步骤

### 1. 克隆项目
```bash
git clone https://github.com/RedteamNotes/WebLoginBrute.git
cd WebLoginBrute
```

### 2. 创建并激活虚拟环境 (强烈推荐)

- **Windows**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **macOS/Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. 安装依赖
在项目根目录下，运行以下命令来安装 WebLoginBrute 及其所有依赖项：
```bash
pip install .
```

> **提示**: 如果安装速度较慢，可以临时使用国内的 PyPI 镜像源：
> `pip install . -i https://pypi.tuna.tsinghua.edu.cn/simple/`

### 4. 验证安装
运行以下命令，如果能看到帮助信息，则说明安装成功：
```bash
webloginbrute --help
```

## 📦 依赖包
本项目的所有依赖都定义在 `pyproject.toml` 文件中，并通过 `pip install .` 命令自动安装。

核心依赖包括：
- **pydantic**: 用于数据验证和配置管理。
- **requests**: 用于发送 HTTP 请求。
- **beautifulsoup4**: 用于解析 HTML 内容。
- **PyYAML**: 用于解析 YAML 配置文件。
- **psutil**: 用于获取系统性能信息。

## 🚨 故障排除

### Python 版本问题
请确保您的 `python` (或 `python3`) 命令指向的是 3.8 或更高版本的解释器。您可以通过以下命令检查：
```bash
python --version
```
如果系统中有多个 Python 版本，请确保在创建虚拟环境和安装时使用的是正确的版本。

## 📞 获取帮助

如果遇到安装问题，请：
1. 仔细检查是否满足系统要求。
2. 确认是否已激活虚拟环境。
3. 搜索项目中的 [GitHub Issues](https://github.com/RedteamNotes/WebLoginBrute/issues)。
4. 如果问题仍然存在，请提交一个新的 Issue。

---

**⚠️ 重要提醒**: 请确保在授权范围内使用本工具，遵守相关法律法规。 