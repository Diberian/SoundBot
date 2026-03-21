# SoundMind LLM 自然语言检索功能

## 功能概述

通过配置本地 LLM（LM Studio / Ollama）或外部 API，实现自然语言语义搜索音效库。

## 使用方法

### 1. 配置 LLM

点击导航栏的「设置」→「AI 设置」，选择 LLM 模型标签页：

- **LM Studio**：本地运行大模型，地址 `http://localhost:1234/v1`
- **Ollama**：本地运行大模型，地址 `http://localhost:11434/v1`
- **外部 API**：使用 OpenAI 兼容格式的外部 API

### 2. 配置 Embedding

在 Embedding 模型标签页选择：

- **默认配置**：使用内置的 CLAP 音频-文本嵌入模型（推荐）
- **本地模型**：使用 LM Studio 或 Ollama 的 Embedding 模型
- **外部 API**：使用 OpenAI text-embedding 等外部服务

### 3. 使用 AI 对话

在右侧 AI 助手面板中，用自然语言描述你需要的音效，例如：

- "很闷的撞击声"
- "下雨天在窗户边的雨声"
- "恐怖游戏里突然吓人的音效"

AI 会自动：
1. 分析你的需求
2. 提取关键词
3. 执行语义搜索
4. 在主音效列表中显示结果

### 4. 快捷标签

点击示例标签可快速发送搜索请求。

## 技术架构

```
前端 (index.html)
├── SettingsModal 弹窗
└── AI Chat 面板 (流式响应)
         ↓
后端 (FastAPI)
├── /api/v1/ai/chat (流式对话)
├── /api/v1/ai/config (配置管理)
└── /api/v1/ai/config/test (测试连接)
         ↓
服务层
├── llm_client.py (统一 LLM 调用)
├── llm_config_manager.py (配置管理)
└── ai_chat_service.py (对话逻辑)
         ↓
搜索层
└── search_engine.py (混合搜索)
```

## 配置文件

- `config/ai_config.json`：AI 配置（LLM、Embedding）
- `config/user_config.json`：用户配置（临时文件目录等）

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/ai/chat` | POST | AI 对话（流式返回） |
| `/api/v1/ai/config` | GET | 获取 AI 配置 |
| `/api/v1/ai/config` | POST | 保存 AI 配置 |
| `/api/v1/ai/config/test` | POST | 测试配置连接 |
| `/api/v1/ai/status` | GET | 获取 AI 服务状态 |

## 环境要求

- Python 3.8+
- FastAPI
- requests
- 音效库已建立索引（CLAP 模型）

## 启动后端

```bash
cd backend
python main.py
```
