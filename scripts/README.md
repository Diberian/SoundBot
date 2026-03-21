# 构建脚本

此目录包含用于构建和发布的脚本。

## 自动依赖管理

**GitHub Actions 会自动处理所有依赖：**

1. **Node.js 依赖** - 自动安装 (`npm ci`)
2. **Python 依赖** - 自动创建 venv 并安装 (`pip install -r requirements.txt`)
3. **AI 模型** - 自动下载到 `models/` 目录

用户下载安装包后**无需任何配置**，开箱即用！

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

**注意**：此脚本为备选方案，当前使用 venv 打包方式更简单可靠。

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

# 4. 打包（包含 venv 和模型）
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
2. ✅ 创建 Python venv 并安装依赖
3. ✅ 下载 AI 模型
4. ✅ 打包应用（包含所有依赖）
5. ✅ 发布到 GitHub Releases

用户只需下载安装包即可使用，无需配置环境！

---

## 打包体积预估

| 组件 | 大小 |
|------|------|
| Electron | ~150MB |
| Python venv + 依赖 | ~1GB |
| CLAP 模型 | ~744MB |
| 应用代码 | ~10MB |
| **总计** | **~1.9GB** |

体积较大是因为包含了完整的 Python 环境和 AI 模型，但用户无需任何配置即可使用。
