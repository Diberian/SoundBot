# 🎵 SoundBot - AI 音效管理器

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-orange.svg)](https://github.com/yourusername/soundbot)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Electron](https://img.shields.io/badge/electron-28.x-9feaf9.svg)](https://www.electronjs.org/)

> 用自然语言找到你想要的任何声音 - AI 驱动的智能音效管理器桌面版

![SoundBot Preview](https://via.placeholder.com/800x450/0a0a0a/22c55e?text=SoundBot+AI+Audio+Manager)

---

## ✨ 核心特性

### 🤖 AI 自然语言搜索
- **描述即搜索** - 用自然语言描述音效（如"很闷的撞击声"、"下雨天在窗户边的雨声"）
- **智能关键词提取** - AI 自动分析需求并提取搜索关键词
- **流式响应** - 实时看到 AI 思考和搜索结果

### 🔍 语义向量搜索
- **CLAP 音频-文本对齐模型** - 基于 LAION 的对比学习预训练模型
- **ChromaDB 向量数据库** - 高效的相似度检索，支持大规模音效库
- **增量索引** - 只处理新文件，快速更新音效库

### 🎛️ 多 LLM 支持
| 提供商 | 状态 | 说明 |
|--------|------|------|
| LM Studio | ✅ | 本地部署，隐私优先 |
| Ollama | ✅ | 开源模型，离线使用 |
| OpenAI | ✅ | GPT-4o-mini 等 |
| Claude | ✅ | Anthropic API |
| DeepSeek | ✅ | 国产大模型 |
| Kimi | ✅ | Moonshot API |
| Gemini | ✅ | Google AI |

### 🎨 现代化界面
- **深色/浅色主题** - 一键切换，护眼设计
- **波形可视化** - WaveSurfer.js 实时音频波形
- **多工程管理** - 项目隔离，数据安全
- **国际化支持** - 中英文界面切换

---

## 🏗️ 项目架构

```
SoundBot/
├── 📦 Electron 前端
│   ├── main.js              # 主进程
│   ├── preload.js           # 安全桥接脚本
│   ├── index.html           # 主界面
│   ├── assets/              # 静态资源
│   └── package.json         # 前端依赖
│
├── 🐍 Python 后端
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── core/                # 核心模块
│   │   ├── ai_chat_service.py   # AI 对话服务
│   │   ├── llm_client.py        # 统一 LLM 客户端
│   │   ├── embedder.py          # CLAP 嵌入模型
│   │   ├── indexer.py           # ChromaDB 索引
│   │   ├── searcher.py          # 语义搜索
│   │   ├── scanner.py           # 音频扫描
│   │   └── ...
│   ├── models/              # 数据模型
│   ├── utils/               # 工具函数
│   └── requirements.txt     # Python 依赖
│
└── ⚙️ 配置
    ├── config/
    │   ├── ai_config.json     # AI 配置
    │   └── user_config.json   # 用户配置
    └── db/                    # 数据库目录
```

---

## 🚀 快速开始

### 环境要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| **操作系统** | macOS 10.15 / Win 10 / Ubuntu 20.04 | 最新版本 |
| **内存** | 8 GB | 16 GB+ |
| **存储** | 2 GB 可用空间 | SSD 推荐 |
| **Python** | 3.10 | 3.12 |
| **Node.js** | 18.x | 20.x |

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/soundbot.git
cd soundbot
```

### 2. 安装前端依赖

```bash
npm install
```

### 3. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 4. 启动应用

**开发模式（带开发者工具）:**
```bash
npm run dev
```

**生产模式:**
```bash
npm start
```

---

## 📖 使用指南

### 1. 配置 AI（可选）

点击 **设置 → AI 设置**，配置您的 LLM：

- **本地部署**：LM Studio (`http://localhost:1234/v1`)
- **Ollama**：`http://localhost:11434/v1`
- **云端 API**：OpenAI、Claude、Kimi 等

### 2. 导入音效

- 点击 **导入 → 导入文件夹** 扫描整个音效库
- 支持格式：WAV, MP3, FLAC, AIFF, OGG, M4A, AAC
- 首次索引可能需要几分钟（取决于音效库大小）

### 3. 开始搜索

在右侧 AI 助手面板输入：
> "找一个恐怖游戏里突然吓人的音效"

或直接在搜索框输入关键词进行语义搜索。

---

## 🛠️ 开发指南

### 项目结构详解

#### 前端 (Electron)
- `main.js` - 主进程，管理窗口生命周期、后端启动
- `preload.js` - 预加载脚本，安全暴露 API 给渲染进程
- `index.html` - 主界面，包含所有 UI 组件

#### 后端 (FastAPI)
- `main.py` - API 入口，定义所有端点
- `core/ai_chat_service.py` - AI 对话逻辑，处理自然语言查询
- `core/llm_client.py` - 统一 LLM 客户端，支持多 Provider
- `core/embedder.py` - CLAP 模型封装，音频/文本嵌入
- `core/indexer.py` - ChromaDB 索引管理
- `core/searcher.py` - 语义搜索实现

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `F12` | 打开/关闭开发者工具 |
| `Cmd/Ctrl + N` | 新建工程 |
| `Cmd/Ctrl + O` | 导入文件 |
| `Cmd/Ctrl + Q` | 退出应用 |

### 调试

```bash
# 启用详细日志
DEBUG=* npm run dev

# 后端调试
DEBUG=true python backend/main.py
```

---

## 📦 构建分发

### 构建应用

```bash
npm run build
```

构建输出将在 `dist/` 目录：
- **macOS** - `.dmg` 安装包
- **Windows** - `.exe` 安装程序
- **Linux** - `.AppImage` 应用镜像

### 配置构建选项

在 `package.json` 的 `build` 字段中修改：

```json
{
  "build": {
    "appId": "com.soundbot.app",
    "productName": "SoundBot",
    "directories": {
      "output": "dist"
    }
  }
}
```

---

## 🧪 技术栈

### 前端
- **Electron** - 跨平台桌面框架
- **Tailwind CSS** - 原子化 CSS 框架
- **Lucide Icons** - 现代化图标库
- **WaveSurfer.js** - 音频波形可视化

### 后端
- **FastAPI** - 高性能 Python Web 框架
- **ChromaDB** - 向量数据库
- **Transformers** - HuggingFace 模型库
- **CLAP** - 音频-文本对比学习模型

### AI/ML
- **CLAP (LAION)** - 音频-文本嵌入模型
- **OpenAI API** - GPT 系列模型
- **多种 LLM Provider** - 支持主流大模型 API

---

## 📄 许可证与商标

### 软件许可证

**GPL-3.0** - 详见 [LICENSE](LICENSE) 文件

使用本软件即表示您同意 GPL-3.0 许可证条款。任何衍生作品必须同样以 GPL-3.0 开源。

### 商标声明

**"SoundBot"** 和 SoundBot Logo 是 [Nagisa_Huckrick](https://github.com/Nagisa_Huckrick) 的商标。

本许可证不授予使用商标的权利。未经书面许可，不得：
- 使用 "SoundBot" 作为衍生产品的名称
- 使用 SoundBot Logo 或类似标识
- 暗示与原作者的关联或认可

### 第三方组件许可

本项目使用了以下第三方组件：

| 组件 | 许可证 |
|------|--------|
| CLAP Model | MIT |
| ChromaDB | Apache-2.0 |
| Electron | MIT |
| FastAPI | MIT |
| WaveSurfer.js | BSD-3-Clause |
| Tailwind CSS | MIT |

---

## 🤖 AI 工具致谢

本项目开发过程中使用了以下 AI 编程助手：

- **[Trae](https://www.trae.ai/)** - 主要开发环境，代码生成与重构
- **[Cursor](https://cursor.sh/)** - 代码编辑与调试辅助

> 这是一个完全由 AI 辅助开发的个人项目，展示了现代 AI 工具在软件开发中的强大能力。

---

## 🤝 贡献指南

欢迎提交 Issue 和 PR！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 🙏 致谢

- [LAION CLAP](https://huggingface.co/laion/larger_clap_general) - 音频-文本嵌入模型
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- [WaveSurfer.js](https://wavesurfer-js.org/) - 音频波形可视化
- [Electron](https://www.electronjs.org/) - 跨平台桌面框架
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Python Web 框架
- [UCS](https://universalcategorysystem.com/) - Universal Category System 音效分类系统

---

## 📞 联系我们

- **GitHub Issues**: [提交问题](https://github.com/yourusername/soundbot/issues)
- **Email**: your-email@example.com

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Nagisa_Huckrick">Nagisa_Huckrick (胡杨)</a><br>
  <strong>GPL-3.0 Licensed</strong>
</p>
