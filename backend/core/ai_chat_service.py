# -*- coding: utf-8 -*-
"""
AI 对话服务 - 自然语言音效搜索

功能：
1. 理解用户自然语言查询意图
2. 提取关键词和筛选条件
3. 执行混合搜索（语义 + 关键词）
4. 返回搜索结果和摘要
"""

import json
import time
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass

from utils.logger import get_logger
from core.llm_client import get_llm_client
from core.search_engine import get_optimized_searcher_sync

logger = get_logger(__name__)


# ==================== 系统提示词 ====================

SYSTEM_PROMPT = """你是一个专业的音效搜索助手。

用户会用自然语言描述他们需要的音效，例如：
- "很闷的撞击声"
- "像金属碰撞的那种清脆的声音"
- "下雨天在窗户边的雨声"
- "恐怖游戏里突然吓人的音效"
- "轻柔的钢琴背景音乐"
- "汽车引擎启动的声音"

你需要：
1. 理解用户的搜索意图和情感色彩
2. 提取核心关键词（中英文都要考虑）
3. 分析可能的音频特征（频率、节奏、氛围等）
4. 如果用户提到了时长、格式等筛选条件，也需要提取

返回严格遵循以下 JSON 格式，不要返回其他内容：
{
    "keywords": ["impact", "muffled", "dull"],
    "chinese_keywords": ["闷", "撞击"],
    "description": "用户想找闷击类音效",
    "intent": "用户想要沉闷、有重量感的撞击声",
    "filters": {
        "min_duration": null,
        "max_duration": null,
        "format": null
    }
}

注意：
- keywords 至少要有英文关键词
- 如果用户没有提到时长、格式等条件，filters 中的值设为 null
- 时长单位是秒，例如 30 秒写成 30
"""


@dataclass
class QueryAnalysis:
    """查询分析结果"""
    keywords: List[str]
    chinese_keywords: List[str]
    description: str
    intent: str
    filters: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'QueryAnalysis':
        return cls(
            keywords=data.get("keywords", []),
            chinese_keywords=data.get("chinese_keywords", []),
            description=data.get("description", ""),
            intent=data.get("intent", ""),
            filters=data.get("filters", {})
        )
    
    def to_dict(self) -> dict:
        return {
            "keywords": self.keywords,
            "chinese_keywords": self.chinese_keywords,
            "description": self.description,
            "intent": self.intent,
            "filters": self.filters
        }


@dataclass
class SearchResult:
    """搜索结果项"""
    path: str
    filename: str
    duration: float
    similarity: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "filename": self.filename,
            "duration": self.duration,
            "similarity": self.similarity,
            "metadata": self.metadata
        }


# ==================== AI 对话服务 ====================

class AIChatService:
    """AI 对话服务"""
    
    def __init__(self):
        self._llm_client = None
        self._searcher = None
    
    @property
    def llm_client(self):
        """懒加载 LLM 客户端"""
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client
    
    @property
    def searcher(self):
        """懒加载搜索引擎"""
        if self._searcher is None:
            self._searcher = get_optimized_searcher_sync()
        return self._searcher
    
    def reload(self):
        """重新加载组件"""
        self._llm_client = None
        self._searcher = None
    
    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 20,
        threshold: float = 0.1
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理对话并返回搜索结果
        
        Args:
            message: 用户消息
            conversation_history: 对话历史（可选）
            top_k: 返回结果数量
            threshold: 相似度阈值
            
        Yields:
            Dict 类型的消息：
            - {"type": "thinking", "content": "正在分析..."}
            - {"type": "analyzing", "analysis": QueryAnalysis}
            - {"type": "searching", "query": str, "keywords": List[str]}
            - {"type": "results", "results": List[dict], "count": int, "summary": str}
            - {"type": "error", "content": str}
        """
        try:
            # 1. 发送思考状态
            yield {
                "type": "thinking",
                "content": "正在理解你的需求..."
            }
            
            # 2. 分析用户查询
            analysis = await self._analyze_query(message, conversation_history)
            
            yield {
                "type": "analyzing",
                "analysis": analysis.to_dict(),
                "content": f"提取到关键词：{', '.join(analysis.keywords)}"
            }
            
            # 3. 构建搜索查询
            search_query = " ".join(analysis.keywords)
            if analysis.chinese_keywords:
                search_query += " " + " ".join(analysis.chinese_keywords)
            
            yield {
                "type": "searching",
                "query": search_query,
                "keywords": analysis.keywords,
                "content": f"正在搜索: \"{search_query}\"..."
            }
            
            # 4. 执行搜索
            results = await self._search_sounds(
                query=search_query,
                analysis=analysis,
                top_k=top_k,
                threshold=threshold
            )
            
            # 5. 生成摘要
            summary = await self._generate_summary(message, results, analysis)
            
            # 6. 返回结果
            yield {
                "type": "results",
                "results": [r.to_dict() for r in results],
                "count": len(results),
                "summary": summary,
                "query": search_query,
                "analysis": analysis.to_dict()
            }
            
        except Exception as e:
            logger.error(f"AI 对话处理失败: {e}")
            yield {
                "type": "error",
                "content": f"处理失败: {str(e)}"
            }
    
    async def _analyze_query(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> QueryAnalysis:
        """
        使用 LLM 分析用户查询
        
        Args:
            message: 用户消息
            history: 对话历史
            
        Returns:
            QueryAnalysis 分析结果
        """
        # 构建消息
        messages = []
        
        # 添加对话历史
        if history:
            for h in history[-5:]:  # 只保留最近 5 条
                messages.append(h)
        
        messages.append({"role": "user", "content": message})
        
        # 调用 LLM
        full_response = ""
        
        async for chunk in self.llm_client.chat(
            messages=messages,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3,  # 较低的 temperature 以获得更稳定的 JSON
            max_tokens=512,
            stream=True
        ):
            if chunk["type"] == "content":
                full_response += chunk["content"]
            elif chunk["type"] == "error":
                raise RuntimeError(chunk["content"])
        
        # 解析 JSON
        try:
            # 尝试提取 JSON（可能在 markdown 代码块中）
            json_str = full_response.strip()
            
            # 移除 markdown 代码块标记
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1] if "```" in json_str else json_str
                json_str = json_str.lstrip("json\n").rstrip("```").strip()
            
            data = json.loads(json_str)
            return QueryAnalysis.from_dict(data)
            
        except json.JSONDecodeError as e:
            logger.warning(f"LLM 返回的 JSON 解析失败: {e}, 原始响应: {full_response[:200]}")
            
            # 降级处理：提取关键词并返回
            return self._fallback_analysis(message)
    
    def _fallback_analysis(self, message: str) -> QueryAnalysis:
        """
        降级分析：当 LLM 返回格式错误时使用
        
        简单提取中英文关键词
        """
        import re
        
        keywords = []
        chinese_keywords = []
        
        # 提取中文
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', message)
        chinese_keywords = chinese_chars
        
        # 简单翻译映射
        translations = {
            "雨": "rain",
            "雷": "thunder",
            "风": "wind",
            "撞击": "impact",
            "爆炸": "explosion",
            "爆炸声": "explosion",
            "金属": "metal",
            "汽车": "car",
            "引擎": "engine",
            "钢琴": "piano",
            "恐怖": "horror",
            "音乐": "music",
            "背景": "background",
            "轻": "light",
            "重": "heavy",
            "闷": "muffled",
            "清脆": "crisp",
            "清脆的": "crisp",
            "声音": "sound",
            "音效": "sound effect",
        }
        
        for cn in chinese_keywords:
            for cn_word, en_word in translations.items():
                if cn_word in cn:
                    keywords.append(en_word)
        
        # 如果没有提取到关键词，使用原始消息
        if not keywords:
            keywords = [message]
        
        return QueryAnalysis(
            keywords=list(set(keywords)),
            chinese_keywords=chinese_keywords,
            description=f"搜索: {message}",
            intent=message,
            filters={}
        )
    
    async def _search_sounds(
        self,
        query: str,
        analysis: QueryAnalysis,
        top_k: int,
        threshold: float
    ) -> List[SearchResult]:
        """
        执行音效搜索
        
        Args:
            query: 搜索查询
            analysis: 查询分析结果
            top_k: 返回数量
            threshold: 相似度阈值
            
        Returns:
            搜索结果列表
        """
        # 构建过滤条件
        filters = {}
        
        if analysis.filters.get("min_duration") is not None:
            filters["duration"] = {"$gte": analysis.filters["min_duration"]}
        
        if analysis.filters.get("max_duration") is not None:
            if "duration" in filters:
                filters["duration"]["$lte"] = analysis.filters["max_duration"]
            else:
                filters["duration"] = {"$lte": analysis.filters["max_duration"]}
        
        if analysis.filters.get("format"):
            filters["format"] = analysis.filters["format"]
        
        try:
            # 执行搜索
            raw_results, stats = await self.searcher.search_async(
                query=query,
                top_k=top_k,
                min_similarity=threshold,
                filters=filters if filters else None,
                use_cache=True
            )
            
            # 转换为 SearchResult
            results = []
            for r in raw_results:
                results.append(SearchResult(
                    path=r.file_path,
                    filename=r.filename,
                    duration=r.duration,
                    similarity=r.similarity,
                    metadata=r.metadata
                ))
            
            logger.info(f"AI 搜索完成: 查询='{query}', 结果数={len(results)}, 耗时={stats.get('duration', 0):.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    async def _generate_summary(
        self,
        original_query: str,
        results: List[SearchResult],
        analysis: QueryAnalysis
    ) -> str:
        """
        生成搜索结果摘要
        
        Args:
            original_query: 用户原始查询
            results: 搜索结果
            analysis: 查询分析结果
            
        Returns:
            摘要文本
        """
        count = len(results)
        
        if count == 0:
            return f"抱歉，没有找到与「{original_query}」相关的结果。试试其他描述？"
        
        # 根据结果数量生成不同风格的摘要
        if count == 1:
            return f"找到 1 个相关音效：{results[0].filename}"
        
        # 提取常见特征
        durations = [r.duration for r in results]
        avg_duration = sum(durations) / len(durations)
        
        if avg_duration < 5:
            duration_desc = "短促"
        elif avg_duration < 15:
            duration_desc = "中等长度"
        else:
            duration_desc = "较长"
        
        return f"找到 {count} 个相关音效（{duration_desc}），已按相似度排序"


# ==================== SSE 工具 ====================

async def stream_to_sse(
    generator: AsyncGenerator[Dict[str, Any], None]
) -> AsyncGenerator[str, None]:
    """
    将字典流转换为 SSE 格式
    
    Args:
        generator: 字典流生成器
        
    Yields:
        SSE 格式的字符串
    """
    async for data in generator:
        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    yield "data: {\"type\": \"done\"}\n\n"


# ==================== 全局单例 ====================

_ai_chat_service: Optional[AIChatService] = None


def get_ai_chat_service() -> AIChatService:
    """获取 AI 对话服务单例"""
    global _ai_chat_service
    if _ai_chat_service is None:
        _ai_chat_service = AIChatService()
    return _ai_chat_service


def reset_ai_chat_service():
    """重置 AI 对话服务"""
    global _ai_chat_service
    if _ai_chat_service is not None:
        _ai_chat_service.reload()
