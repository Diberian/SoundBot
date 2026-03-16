"""
CLAP 音频-文本嵌入模型封装

使用微软的 CLAP 模型进行音频和文本的特征提取。
支持音频-文本对齐搜索功能。
"""

import torch
import numpy as np
from typing import Optional
from pathlib import Path

import librosa
import config
from utils.audio_utils import load_audio


class CLIPEmbedder:
    """CLAP 音频-文本嵌入模型封装"""
    
    _instance = None  # 单例模式，避免重复加载模型
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 自动检测设备
        self.device = self._get_device()
        print(f"[Embedder] 加载 CLAP 模型到 {self.device}...")
        
        # 动态导入 transformers，避免启动时卡顿
        from transformers import ClapModel, ClapProcessor
        
        # 使用微软的 CLAP 模型（支持音频-文本对齐）
        self.model = ClapModel.from_pretrained(config.CLAP_MODEL_NAME).to(self.device)
        self.processor = ClapProcessor.from_pretrained(config.CLAP_MODEL_NAME)
        
        self.model.eval()
        self._initialized = True
        print("[Embedder] 模型加载完成")
    
    def _get_device(self) -> torch.device:
        """自动检测可用的计算设备"""
        if torch.cuda.is_available():
            return torch.device("cuda")
        
        # 尝试 MPS（Apple Silicon）
        try:
            if torch.backends.mps.is_available():
                return torch.device("mps")
        except AttributeError:
            pass
        
        return torch.device("cpu")
    
    def audio_to_embedding(self, audio_path: str) -> np.ndarray:
        """
        将音频文件转换为 embedding 向量
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            归一化的 embedding 向量
        """
        try:
            # 加载音频（支持各种格式）
            audio, sr = librosa.load(audio_path, sr=48000, mono=True)
            
            # 限制音频长度（CLAP 通常处理 10-30 秒最佳）
            max_samples = 30 * 48000  # 30秒
            if len(audio) > max_samples:
                audio = audio[:max_samples]
            
            # 使用 processor 处理
            inputs = self.processor(
                audios=[audio], 
                sampling_rate=48000, 
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.get_audio_features(**inputs)
                embedding = outputs.cpu().numpy()[0]
            
            # 归一化（方便余弦相似度计算）
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            raise RuntimeError(f"[Embedder] 处理 {audio_path} 失败: {e}")
    
    def text_to_embedding(self, text: str) -> np.ndarray:
        """
        将文本查询转换为 embedding 向量
        
        Args:
            text: 文本查询
            
        Returns:
            归一化的 embedding 向量
        """
        try:
            inputs = self.processor(
                text=[text], 
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.get_text_features(**inputs)
                embedding = outputs.cpu().numpy()[0]
            
            # 归一化
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            raise RuntimeError(f"[Embedder] 文本嵌入失败: {e}")
    
    def get_embedding_dim(self) -> int:
        """获取 embedding 向量的维度"""
        # CLAP 模型固定维度为 512
        return 512


# 全局单例
_embedder: Optional[CLIPEmbedder] = None


def get_embedder() -> CLIPEmbedder:
    """获取 Embedder 单例（延迟加载）"""
    global _embedder
    if _embedder is None:
        _embedder = CLIPEmbedder()
    return _embedder


def reset_embedder() -> None:
    """重置 Embedder 单例（用于测试或重新加载模型）"""
    global _embedder
    _embedder = None
