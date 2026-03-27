# 构建脚本

此目录包含用于构建和发布的脚本。

## 自动依赖管理

**GitHub Actions 会自动处理所有依赖：**

1. **Node.js 依赖** - 自动安装 (`npm ci`)
2. **Python 依赖** - 自动安装并打包到 PyInstaller 后端
3. **AI 模型** - 自动下载到 `models/` 目录

应用安装包包含 Electron 前端和 PyInstaller 后端，AI 模型需要首次额外下载一次。

---

## 脚本说明

### download_models.py
下载 AI 模型到本地 `models/` 目录。

```bash
# 使用虚拟环境中的 Python 运行
cd backend
source venv/bin/activate  # macOS/Linux
# 或 .\venv\Scripts\activate  # Windows
cd ..
python scripts/download_models.py
```

### build_backend.py（可选）
使用 PyInstaller 将 Python 后端打包为独立可执行文件。

---

## 本地打包步骤

### macOS

```bash
# 1. 安装 Node 依赖
npm ci

# 2. 创建 Python 虚拟环境并安装依赖
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 3. 下载 AI 模型
python scripts/download_models.py

# 4. 打包（应用包包含 PyInstaller 后端，不包含 models）
npm run build:mac

# 输出: dist/SoundBot-0.1.0-alpha.dmg
```

### Windows

```powershell
# 1. 安装 Node 依赖
npm ci

# 2. 创建 Python 虚拟环境并安装依赖
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cd ..

# 3. 下载 AI 模型
python scripts/download_models.py

# 4. 打包
npm run build:win

# 输出: dist/SoundBot-0.1.0-alpha.exe
```

---

## 自动构建（GitHub Actions）

推送标签自动触发构建：

```bash
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions 会自动：
1. ✅ 安装 Node.js 依赖
2. ✅ 安装 Python 依赖并构建 PyInstaller 后端
3. ✅ 下载 AI 模型
4. ✅ 发布应用安装包与独立的 models.zip
5. ✅ 发布到 GitHub Releases

用户需下载安装包，并在首次启动前额外下载 models.zip。

---

## 打包体积预估

| 组件 | 大小 |
|------|------|
| Electron | ~150MB |
| PyInstaller 后端 | ~300MB-800MB |
| CLAP 模型 | ~744MB |
| 应用代码 | ~10MB |
| **总计** | **~1.2GB-1.6GB** |

体积较大主要来自 PyInstaller 后端和 AI 模型，模型作为独立资源发布。
