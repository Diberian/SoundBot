# -*- coding: utf-8 -*-
# SoundBot - AI 音效管理器
# Copyright (C) 2026 Nagisa_Huckrick (胡杨)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
LRU 音频内存缓存模块

用于缓存已解码的音频数据（numpy数组），提高重复播放的响应速度。
当缓存超过最大容量时，自动踢出最久未访问的文件。

工作流程：
1. 用户点击某文件
2. 查询 LRU 缓存
3. 命中 → 直接使用，更新 last_access 时间
4. 未命中 → 从磁盘读取解码 → 放入缓存
5. 缓存超过100个 → 自动踢出 last_access 最早的文件
"""

import time
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

import numpy as np

logger = None


def _get_logger():
    """延迟获取 logger，避免循环导入"""
    global logger
    if logger is None:
        from utils.logger import get_logger
        logger = get_logger()
    return logger


@dataclass
class AudioCacheEntry:
    """音频缓存条目"""
    audio_data: np.ndarray          # 解码后的音频数据 (numpy数组)
    sample_rate: int                # 采样率
    duration: float                  # 时长（秒）
    last_access: float               # 最后访问时间戳
    file_size: int                   # 原始文件大小（字节）
    channels: int = 1               # 声道数

    @property
    def memory_size(self) -> int:
        """估算内存占用（字节）"""
        if self.audio_data is None:
            return 0
        # float32 = 4 bytes per sample
        return self.audio_data.nbytes

    def update_access(self):
        """更新访问时间"""
        self.last_access = time.time()


class LRUCache:
    """
    LRU 内存缓存

    特性：
    - 基于 OrderedDict 实现 O(1) 复杂度的 LRU 操作
    - 线程安全
    - 最大容量 20 个文件（降低内存占用）
    - 支持内存上限限制（默认 500MB）
    - 支持缓存统计
    """

    MAX_SIZE = 20  # 最大缓存文件数（从100降低到20，减少内存占用）
    MAX_MEMORY_MB = 500  # 最大内存占用 500MB

    def __init__(self, max_size: int = MAX_SIZE, max_memory_mb: int = MAX_MEMORY_MB):
        """
        初始化 LRU 缓存

        Args:
            max_size: 最大缓存文件数，默认 20
            max_memory_mb: 最大内存占用(MB)，默认 500
        """
        self._cache: OrderedDict[str, AudioCacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._max_size = max_size
        self._max_memory_mb = max_memory_mb
        self._hits = 0        # 命中次数
        self._misses = 0      # 未命中次数
        self._total_evictions = 0  # 总踢出次数
        _get_logger().info(f"LRUCache 初始化完成，最大容量: {max_size} 个文件, 内存上限: {max_memory_mb}MB")

    def get(self, file_path: str) -> Optional[AudioCacheEntry]:
        """
        获取缓存条目

        如果命中，更新访问时间为当前时间（移到链表末尾）

        Args:
            file_path: 文件路径（作为缓存 key）

        Returns:
            缓存条目，如果未命中则返回 None
        """
        with self._lock:
            entry = self._cache.get(file_path)

            if entry is not None:
                # 命中：更新访问时间并移到末尾
                entry.update_access()
                self._cache.move_to_end(file_path)
                self._hits += 1
                _get_logger().debug(f"缓存命中: {file_path}")
                return entry
            else:
                # 未命中
                self._misses += 1
                _get_logger().debug(f"缓存未命中: {file_path}")
                return None

    def _get_current_memory_mb(self) -> float:
        """获取当前缓存占用的内存（MB）"""
        return sum(e.memory_size for e in self._cache.values()) / (1024 * 1024)

    def put(self, file_path: str, entry: AudioCacheEntry) -> None:
        """
        放入缓存条目

        如果 key 已存在，更新值并移到末尾
        如果缓存满或超过内存上限，先踢出最久未访问的条目

        Args:
            file_path: 文件路径
            entry: 缓存条目
        """
        with self._lock:
            # 如果已存在，先删除旧条目
            if file_path in self._cache:
                del self._cache[file_path]

            entry_memory_mb = entry.memory_size / (1024 * 1024)

            # 检查内存上限：踢出足够多的旧条目
            current_memory_mb = self._get_current_memory_mb()
            while (current_memory_mb + entry_memory_mb > self._max_memory_mb and
                   len(self._cache) > 0):
                self._evict_oldest()
                current_memory_mb = self._get_current_memory_mb()

            # 检查数量上限
            while len(self._cache) >= self._max_size:
                self._evict_oldest()

            # 添加新条目
            entry.last_access = time.time()
            self._cache[file_path] = entry
            self._cache.move_to_end(file_path)

            _get_logger().debug(
                f"缓存已添加: {file_path}, 当前大小: {len(self._cache)}, "
                f"内存占用: {self._get_current_memory_mb():.1f}MB"
            )

    def _evict_oldest(self) -> Optional[str]:
        """
        踢出最久未访问的条目

        Returns:
            被踢出的文件路径，如果缓存为空则返回 None
        """
        if not self._cache:
            return None

        # OrderedDict 的 first item 就是最久未访问的
        oldest_key, oldest_entry = self._cache.popitem(last=False)
        self._total_evictions += 1

        _get_logger().debug(
            f"缓存已满，踢出最旧条目: {oldest_key}, "
            f"访问时间: {oldest_entry.last_access}"
        )

        return oldest_key

    def remove(self, file_path: str) -> bool:
        """
        手动移除缓存条目

        Args:
            file_path: 文件路径

        Returns:
            是否成功移除
        """
        with self._lock:
            if file_path in self._cache:
                del self._cache[file_path]
                return True
            return False

    def clear(self) -> int:
        """
        清空所有缓存

        Returns:
            被清空的条目数量
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            _get_logger().info(f"缓存已清空，共 {count} 个条目")
            return count

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            包含统计信息的字典
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            # 计算总内存占用
            total_memory = sum(entry.memory_size for entry in self._cache.values())

            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "total_requests": total_requests,
                "hit_rate": round(hit_rate, 4),
                "total_evictions": self._total_evictions,
                "total_memory_bytes": total_memory,
                "total_memory_mb": round(total_memory / (1024 * 1024), 2),
                "entries": [
                    {
                        "path": path,
                        "memory_mb": round(entry.memory_size / (1024 * 1024), 2),
                        "last_access": entry.last_access
                    }
                    for path, entry in list(self._cache.items())[-5:]  # 最近5个
                ]
            }

    def reset_stats(self):
        """重置统计数据（保留缓存内容）"""
        with self._lock:
            self._hits = 0
            self._misses = 0
            self._total_evictions = 0

    def __len__(self) -> int:
        """返回当前缓存大小"""
        with self._lock:
            return len(self._cache)

    def __contains__(self, file_path: str) -> bool:
        """检查文件是否在缓存中"""
        with self._lock:
            return file_path in self._cache


# ========== 全局单例 ==========

_cache_instance: Optional[LRUCache] = None
_cache_lock = threading.Lock()


def get_audio_cache() -> LRUCache:
    """
    获取音频缓存单例

    Returns:
        LRUCache 实例
    """
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = LRUCache()
    return _cache_instance


def reset_audio_cache() -> None:
    """重置缓存单例（用于应用关闭或测试）"""
    global _cache_instance
    if _cache_instance is not None:
        with _cache_lock:
            if _cache_instance is not None:
                _cache_instance.clear()
                _cache_instance = None


def preload_audio(file_path: str) -> Optional[AudioCacheEntry]:
    """
    预加载音频文件到缓存

    Args:
        file_path: 音频文件路径

    Returns:
        缓存条目，如果加载失败则返回 None
    """
    import librosa
    import soundfile as sf
    from pathlib import Path

    cache = get_audio_cache()

    # 如果已经在缓存中，直接返回
    if file_path in cache:
        return cache.get(file_path)

    try:
        path = Path(file_path)
        if not path.exists():
            return None

        # 加载音频
        audio, sr = librosa.load(str(path), sr=None, mono=False)

        # 获取音频信息
        info = sf.info(str(path))

        # 创建缓存条目
        entry = AudioCacheEntry(
            audio_data=audio,
            sample_rate=sr,
            duration=info.duration,
            file_size=path.stat().st_size,
            channels=info.channels
        )

        # 放入缓存
        cache.put(file_path, entry)

        _get_logger().info(f"预加载完成: {file_path}")
        return entry

    except Exception as e:
        _get_logger().error(f"预加载失败 {file_path}: {e}")
        return None
