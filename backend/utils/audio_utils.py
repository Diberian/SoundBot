# -*- coding: utf-8 -*-
"""
音频工具函数

提供音频处理相关的工具函数，包括音频加载、格式转换等。
"""

import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from typing import Tuple, Optional

import config


def load_audio(
    file_path: str, 
    sr: int = 44100, 
    mono: bool = True
) -> Tuple[np.ndarray, int]:
    """
    加载音频文件
    
    Args:
        file_path: 音频文件路径
        sr: 目标采样率，None 表示保持原始采样率
        mono: 是否转换为单声道
        
    Returns:
        (音频数据, 采样率)
    """
    try:
        audio, sample_rate = librosa.load(file_path, sr=sr, mono=mono)
        return audio, sample_rate
    except Exception as e:
        raise RuntimeError(f"加载音频文件失败 {file_path}: {e}")


def save_audio(
    file_path: str, 
    audio: np.ndarray, 
    sample_rate: int = 44100
) -> None:
    """
    保存音频文件
    
    Args:
        file_path: 输出文件路径
        audio: 音频数据
        sample_rate: 采样率
    """
    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 确保音频数据类型正确
    if audio.dtype != np.float32 and audio.dtype != np.float64:
        audio = audio.astype(np.float32)
    
    sf.write(str(output_path), audio, sample_rate)


def get_audio_duration(file_path: str) -> float:
    """
    获取音频文件时长（秒）
    
    Args:
        file_path: 音频文件路径
        
    Returns:
        时长（秒）
    """
    info = sf.info(file_path)
    return info.duration


def get_audio_info(file_path: str) -> dict:
    """
    获取音频文件的详细信息
    
    Args:
        file_path: 音频文件路径
        
    Returns:
        包含音频信息的字典
    """
    info = sf.info(file_path)
    return {
        "duration": info.duration,
        "sample_rate": info.samplerate,
        "channels": info.channels,
        "format": info.format,
        "subtype": info.subtype,
        "frames": info.frames
    }


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    """
    归一化音频到 [-1, 1] 范围
    
    Args:
        audio: 音频数据
        
    Returns:
        归一化后的音频数据
    """
    max_val = np.abs(audio).max()
    if max_val > 0:
        audio = audio / max_val
    return audio


def resample_audio(
    audio: np.ndarray, 
    orig_sr: int, 
    target_sr: int
) -> np.ndarray:
    """
    重采样音频
    
    Args:
        audio: 音频数据
        orig_sr: 原始采样率
        target_sr: 目标采样率
        
    Returns:
        重采样后的音频数据
    """
    return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)


def stereo_to_mono(audio: np.ndarray) -> np.ndarray:
    """
    将立体声转换为单声道
    
    Args:
        audio: 音频数据
        
    Returns:
        单声道音频数据
    """
    if audio.ndim == 1:
        return audio
    return librosa.to_mono(audio)


def trim_silence(
    audio: np.ndarray, 
    top_db: int = 30
) -> np.ndarray:
    """
    去除音频前后静音
    
    Args:
        audio: 音频数据
        top_db: 静音阈值（分贝）
        
    """
    return librosa.effects.trim(audio, top_db=top_db)[0]


def is_supported_format(file_path: str) -> bool:
    """
    检查文件是否为支持的音频格式
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否支持
    """
    ext = Path(file_path).suffix.lower()
    return ext in config.SUPPORTED_FORMATS


def format_duration(seconds: float) -> str:
    """
    格式化时长为 mm:ss 格式
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化后的字符串
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化后的字符串（如 "1.5 MB"）
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
