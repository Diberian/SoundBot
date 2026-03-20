"""
音频文件扫描模块

扫描指定文件夹及其子文件夹，识别音频文件并提取元数据。
"""

import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import librosa
import soundfile as sf
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# 支持的音频格式
SUPPORTED_AUDIO_FORMATS = {'.wav', '.mp3', '.aac', '.flac', '.aiff', '.ogg', '.m4a'}


class AudioFile(BaseModel):
    """音频文件信息模型"""
    path: str
    filename: str
    duration: float
    sample_rate: int
    channels: int
    format: str
    size: int
    folder_path: str = ""  # 文件所在文件夹路径（相对于导入根目录）
    # 文件名解析的元数据
    parsed_name: str = ""  # 解析后的文件名（去除扩展名和分隔符）
    name_tokens: List[str] = []  # 文件名分词
    name_description: str = ""  # 从文件名生成的描述
    # 音频元数据标签
    metadata_tags: Dict[str, Any] = {}  # 音频文件内置元数据标签


class FolderNode(BaseModel):
    """文件夹节点模型（用于构建树形结构）"""
    name: str
    path: str  # 完整路径
    relative_path: str  # 相对于导入根目录的路径
    children: List['FolderNode'] = []  # 子文件夹
    file_count: int = 0  # 该文件夹下的文件数量（包含子文件夹）

    class Config:
        arbitrary_types_allowed = True


class AudioScanner:
    """音频文件扫描器"""

    def __init__(self):
        self.supported_formats = SUPPORTED_AUDIO_FORMATS

    def scan(self, folder_path: str, recursive: bool = True) -> List[AudioFile]:
        """
        扫描指定文件夹中的音频文件

        Args:
            folder_path: 要扫描的文件夹路径
            recursive: 是否递归扫描子文件夹

        Returns:
            音频文件列表，包含完整路径和元数据
        """
        folder = Path(folder_path)

        if not folder.exists():
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")

        if not folder.is_dir():
            raise NotADirectoryError(f"路径不是文件夹: {folder_path}")

        audio_files = []
        scanned_dirs = []
        skipped_files = []
        error_files = []

        logger.info(f"[SCANNER] 开始扫描文件夹: {folder_path}, 递归: {recursive}")
        print(f"[SCANNER] 开始扫描文件夹: {folder_path}, 递归: {recursive}", flush=True)

        if recursive:
            # 递归扫描所有子文件夹
            logger.info(f"[SCANNER] 使用 os.walk 开始递归扫描...")
            print(f"[SCANNER] 使用 os.walk 开始递归扫描...", flush=True)
            print(f"[SCANNER] 文件夹对象类型: {type(folder)}, 路径: {folder}", flush=True)
            print(f"[SCANNER] 文件夹是否存在: {folder.exists()}", flush=True)
            print(f"[SCANNER] 文件夹是否可读: {os.access(folder, os.R_OK)}", flush=True)
            
            # 尝试列出根目录内容
            try:
                root_contents = list(folder.iterdir())
                print(f"[SCANNER] 根目录内容数量: {len(root_contents)}", flush=True)
                for item in root_contents[:10]:  # 只显示前10个
                    item_type = "文件夹" if item.is_dir() else "文件"
                    print(f"[SCANNER]   - {item.name} ({item_type})", flush=True)
            except Exception as e:
                print(f"[SCANNER] ❌ 无法列出根目录内容: {e}", flush=True)
            
            walk_count = 0
            for root, dirs, files in os.walk(folder):
                walk_count += 1
                scanned_dirs.append(root)
                logger.info(f"[SCANNER] 扫描子文件夹: {root}, 文件数: {len(files)}, 子目录数: {len(dirs)}")
                print(f"[SCANNER] [{walk_count}] 扫描: {root}", flush=True)
                print(f"[SCANNER]      文件: {len(files)} 个, 子目录: {len(dirs)} 个", flush=True)
                if dirs:
                    print(f"[SCANNER]      子目录列表: {dirs}", flush=True)
                
                # 检查每个子目录是否可访问
                for d in dirs:
                    subdir_path = Path(root) / d
                    try:
                        is_accessible = subdir_path.exists() and subdir_path.is_dir() and os.access(subdir_path, os.R_OK)
                        print(f"[SCANNER]      检查子目录 '{d}': 可访问={is_accessible}", flush=True)
                        if not is_accessible:
                            logger.warning(f"[SCANNER] 子目录可能无法访问: {subdir_path}")
                            print(f"[SCANNER]      ⚠️ 子目录可能无法访问: {subdir_path}", flush=True)
                    except Exception as e:
                        logger.error(f"[SCANNER] 检查子目录权限失败 {subdir_path}: {e}")
                        print(f"[SCANNER]      ❌ 检查子目录权限失败: {e}", flush=True)
                
                for filename in files:
                    file_path = Path(root) / filename
                    file_ext = file_path.suffix.lower()
                    
                    # 记录所有被检查的文件
                    logger.debug(f"[SCANNER] 检查文件: {file_path}, 扩展名: {file_ext}")
                    
                    # 检查格式是否支持
                    if file_ext not in self.supported_formats:
                        skipped_files.append(f"{file_path} (不支持格式: {file_ext})")
                        logger.debug(f"[SCANNER] 跳过不支持的格式: {file_path}")
                        continue
                    
                    audio_file = self._process_file(file_path)
                    if audio_file:
                        audio_files.append(audio_file)
                        logger.info(f"[SCANNER] 成功处理音频文件: {file_path}")
                        print(f"[SCANNER] ✓ 成功处理: {file_path.name}", flush=True)
                    else:
                        error_files.append(str(file_path))
                        logger.warning(f"[SCANNER] 处理文件失败: {file_path}")
                        print(f"[SCANNER] ✗ 处理失败: {file_path.name}", flush=True)
        else:
            # 只扫描当前文件夹
            logger.info(f"[SCANNER] 非递归模式，仅扫描当前文件夹")
            for file_path in folder.iterdir():
                if file_path.is_file():
                    file_ext = file_path.suffix.lower()
                    logger.debug(f"[SCANNER] 检查文件: {file_path}, 扩展名: {file_ext}")
                    
                    if file_ext not in self.supported_formats:
                        skipped_files.append(f"{file_path} (不支持格式: {file_ext})")
                        continue
                    
                    audio_file = self._process_file(file_path)
                    if audio_file:
                        audio_files.append(audio_file)
                        logger.info(f"[SCANNER] 成功处理音频文件: {file_path}")

        # 输出扫描统计
        logger.info(f"[SCANNER] 扫描完成统计:")
        logger.info(f"  - 扫描的文件夹数: {len(scanned_dirs)}")
        logger.info(f"  - 跳过的文件数: {len(skipped_files)}")
        logger.info(f"  - 处理失败的文件数: {len(error_files)}")
        logger.info(f"  - 成功处理的音频文件数: {len(audio_files)}")
        logger.info(f"  - 扫描的文件夹列表: {scanned_dirs}")
        
        print(f"[SCANNER] ===== 扫描完成统计 =====", flush=True)
        print(f"[SCANNER] 扫描的文件夹数: {len(scanned_dirs)}", flush=True)
        print(f"[SCANNER] 跳过的文件数: {len(skipped_files)}", flush=True)
        print(f"[SCANNER] 处理失败的文件数: {len(error_files)}", flush=True)
        print(f"[SCANNER] 成功处理的音频文件数: {len(audio_files)}", flush=True)
        print(f"[SCANNER] 扫描的文件夹列表:", flush=True)
        for d in scanned_dirs:
            print(f"  - {d}", flush=True)
        
        if skipped_files:
            print(f"[SCANNER] 跳过的文件 (前10个):", flush=True)
            for f in skipped_files[:10]:
                print(f"  - {f}", flush=True)
        
        if error_files:
            print(f"[SCANNER] 处理失败的文件 (前10个):", flush=True)
            for f in error_files[:10]:
                print(f"  - {f}", flush=True)

        return audio_files

    def scan_with_structure(self, folder_path: str, recursive: bool = True) -> tuple[List[AudioFile], FolderNode]:
        """
        扫描文件夹并返回文件列表和文件夹结构

        Args:
            folder_path: 要扫描的文件夹路径
            recursive: 是否递归扫描子文件夹

        Returns:
            (音频文件列表, 文件夹树形结构根节点)
        """
        folder = Path(folder_path)
        root_name = folder.name or folder_path

        # 先扫描所有文件
        audio_files = self.scan(folder_path, recursive)

        # 构建文件夹树形结构
        root_node = FolderNode(
            name=root_name,
            path=str(folder.absolute()),
            relative_path="",
            children=[],
            file_count=len(audio_files)
        )

        # 按文件夹路径分组文件
        folder_files = {}
        for audio_file in audio_files:
            file_path = Path(audio_file.path)
            parent_path = str(file_path.parent)
            if parent_path not in folder_files:
                folder_files[parent_path] = []
            folder_files[parent_path].append(audio_file)

        # 构建文件夹层级结构
        folder_nodes = {str(folder.absolute()): root_node}

        for parent_path, files in folder_files.items():
            parent = Path(parent_path)

            # 确保父文件夹节点存在
            current_path = str(parent.absolute())
            if current_path not in folder_nodes:
                # 创建从根到当前文件夹的路径
                relative = parent.relative_to(folder)
                parts = list(relative.parts) if relative.parts else []

                current_node = root_node
                current_build_path = str(folder.absolute())

                for part in parts:
                    current_build_path = os.path.join(current_build_path, part)

                    if current_build_path not in folder_nodes:
                        new_node = FolderNode(
                            name=part,
                            path=current_build_path,
                            relative_path=str(Path(current_build_path).relative_to(folder)),
                            children=[],
                            file_count=0
                        )
                        folder_nodes[current_build_path] = new_node
                        current_node.children.append(new_node)

                    current_node = folder_nodes[current_build_path]

            # 更新文件计数
            node = folder_nodes.get(current_path, root_node)
            node.file_count = len(files)

            # 为每个文件设置 folder_path
            for audio_file in files:
                try:
                    file_parent = Path(audio_file.path).parent
                    relative_folder = str(file_parent.relative_to(folder))
                    audio_file.folder_path = relative_folder if relative_folder != "." else ""
                except ValueError:
                    audio_file.folder_path = ""

        # 递归计算每个节点的总文件数（包含子文件夹）
        def calc_file_count(node: FolderNode) -> int:
            total = node.file_count
            for child in node.children:
                total += calc_file_count(child)
            node.file_count = total
            return total

        calc_file_count(root_node)

        logger.info(f"[SCANNER] 文件夹结构构建完成: {root_name}, 共 {len(audio_files)} 个文件")
        return audio_files, root_node

    def _parse_filename(self, filename: str) -> tuple[str, List[str], str]:
        """
        解析文件名，提取有意义的词汇和描述

        Args:
            filename: 文件名（不含路径）

        Returns:
            (解析后的名称, 分词列表, 生成的描述)
        """
        # 去除扩展名
        name_without_ext = os.path.splitext(filename)[0]

        # 替换常见分隔符为空格
        separators = r'[_\-\s\.]+'
        parsed = re.sub(separators, ' ', name_without_ext)

        # 分词
        tokens = [t.strip() for t in parsed.split() if t.strip()]

        # 过滤掉纯数字和过短的词
        meaningful_tokens = []
        for token in tokens:
            # 保留长度大于1的词，或者包含字母的词
            if len(token) > 1 or any(c.isalpha() for c in token):
                # 去除常见无意义后缀
                if token.lower() not in ['wav', 'mp3', 'flac', 'aif', 'aiff', 'm4a', 'ogg']:
                    meaningful_tokens.append(token)

        # 生成描述
        description = ' '.join(meaningful_tokens)

        return parsed, meaningful_tokens, description

    def _extract_wav_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        提取 WAV 文件的 BWF/iXML 元数据

        Args:
            file_path: WAV 文件路径

        Returns:
            元数据字典
        """
        metadata = {}
        try:
            # 使用 wave 模块读取基本 RIFF 信息
            import wave
            with wave.open(str(file_path), 'rb') as wav_file:
                # 尝试读取 INFO 块
                # 注意：标准 wave 模块不支持扩展块，需要手动解析
                pass

            # 使用 soundfile 读取更多元数据
            info = sf.info(str(file_path))

            # 尝试读取 BWF 元数据 (Broadcast Wave Format)
            if hasattr(info, 'comment') and info.comment:
                metadata['comment'] = info.comment
                metadata['description'] = info.comment

            # 使用 mutagen 读取 WAV 的 BWF 标签
            try:
                from mutagen.wave import WAVE
                audio = WAVE(str(file_path))

                # 读取 BWF 特有的标签
                if hasattr(audio, 'tags') and audio.tags:
                    for key, value in audio.tags.items():
                        if value:
                            metadata[key] = str(value)

                # 尝试读取 BWF 的 iXML 块
                if hasattr(audio, 'info') and hasattr(audio.info, 'xml_data'):
                    xml_data = audio.info.xml_data
                    if xml_data:
                        metadata['ixml'] = xml_data.decode('utf-8', errors='ignore')[:1000]  # 限制长度

            except ImportError:
                pass
            except Exception as e:
                logger.debug(f"读取 WAV BWF 标签失败 {file_path}: {e}")

            # 尝试使用 tinytag 读取更多元数据
            try:
                from tinytag import TinyTag
                tag = TinyTag.get(str(file_path))

                if tag.title:
                    metadata['title'] = tag.title
                if tag.artist:
                    metadata['artist'] = tag.artist
                if tag.album:
                    metadata['album'] = tag.album
                if tag.comment:
                    metadata['comment'] = tag.comment
                if tag.track:
                    metadata['track'] = str(tag.track)
                if tag.year:
                    metadata['year'] = str(tag.year)
                if tag.genre:
                    metadata['genre'] = tag.genre

            except ImportError:
                pass
            except Exception as e:
                logger.debug(f"读取 WAV tinytag 失败 {file_path}: {e}")

        except Exception as e:
            logger.debug(f"提取 WAV 元数据失败 {file_path}: {e}")

        return metadata

    def _extract_audio_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        提取音频文件的元数据标签

        Args:
            file_path: 文件路径

        Returns:
            元数据字典
        """
        metadata = {}
        suffix = file_path.suffix.lower()

        try:
            # 使用 soundfile 读取元数据
            info = sf.info(str(file_path))
            if hasattr(info, 'comment') and info.comment:
                metadata['comment'] = info.comment

            # WAV 文件特殊处理（BWF/iXML）
            if suffix == '.wav':
                wav_metadata = self._extract_wav_metadata(file_path)
                metadata.update(wav_metadata)

            # MP3 文件
            elif suffix == '.mp3':
                try:
                    from mutagen.mp3 import MP3
                    audio = MP3(str(file_path))
                    if audio.tags:
                        for key, value in audio.tags.items():
                            if value:
                                metadata[key] = str(value)
                except ImportError:
                    pass

            # FLAC/OGG 文件
            elif suffix in ['.flac', '.ogg']:
                try:
                    from mutagen.flac import FLAC
                    from mutagen.oggvorbis import OggVorbis
                    if suffix == '.flac':
                        audio = FLAC(str(file_path))
                    else:
                        audio = OggVorbis(str(file_path))
                    if audio.tags:
                        for key, value in audio.tags.items():
                            if value:
                                metadata[key] = str(value[0]) if isinstance(value, list) else str(value)
                except ImportError:
                    pass

            # AIFF 文件
            elif suffix in ['.aiff', '.aif']:
                try:
                    from mutagen.aiff import AIFF
                    audio = AIFF(str(file_path))
                    if audio.tags:
                        for key, value in audio.tags.items():
                            if value:
                                metadata[key] = str(value)
                except ImportError:
                    pass

            # M4A/AAC 文件
            elif suffix in ['.m4a', '.aac']:
                try:
                    from mutagen.mp4 import MP4
                    audio = MP4(str(file_path))
                    if audio.tags:
                        for key, value in audio.tags.items():
                            if value:
                                metadata[key] = str(value[0]) if isinstance(value, list) else str(value)
                except ImportError:
                    pass

        except Exception as e:
            logger.debug(f"提取音频元数据失败 {file_path}: {e}")

        return metadata

    def _process_file(self, file_path: Path) -> Optional[AudioFile]:
        """
        处理单个音频文件，提取元数据

        Args:
            file_path: 文件路径

        Returns:
            音频文件信息，如果不支持则返回 None
        """
        # 检查文件格式
        if file_path.suffix.lower() not in self.supported_formats:
            return None

        try:
            # 获取文件基本信息
            stat = file_path.stat()

            # 解析文件名
            parsed_name, name_tokens, name_description = self._parse_filename(file_path.name)

            # 提取音频元数据标签
            metadata_tags = self._extract_audio_metadata(file_path)

            # 使用 soundfile 获取音频信息（更高效）
            info = sf.info(str(file_path))

            return AudioFile(
                path=str(file_path.absolute()),
                filename=file_path.name,
                duration=info.duration,
                sample_rate=info.samplerate,
                channels=info.channels,
                format=info.format,
                size=stat.st_size,
                parsed_name=parsed_name,
                name_tokens=name_tokens,
                name_description=name_description,
                metadata_tags=metadata_tags
            )
        except Exception as e:
            # 如果 soundfile 失败，尝试使用 librosa
            try:
                stat = file_path.stat()
                y, sr = librosa.load(str(file_path), sr=None, mono=False)

                # 计算时长
                duration = librosa.get_duration(y=y, sr=sr)

                # 确定声道数
                channels = 1 if y.ndim == 1 else y.shape[0]

                # 解析文件名
                parsed_name, name_tokens, name_description = self._parse_filename(file_path.name)

                # 提取音频元数据标签
                metadata_tags = self._extract_audio_metadata(file_path)

                return AudioFile(
                    path=str(file_path.absolute()),
                    filename=file_path.name,
                    duration=duration,
                    sample_rate=sr,
                    channels=channels,
                    format=file_path.suffix.lower()[1:],
                    size=stat.st_size,
                    parsed_name=parsed_name,
                    name_tokens=name_tokens,
                    name_description=name_description,
                    metadata_tags=metadata_tags
                )
            except Exception as e:
                # 跳过无法读取的文件
                logger.warning(f"无法读取音频文件 {file_path}: {e}")
                return None

    def is_audio_file(self, file_path: str) -> bool:
        """
        检查文件是否为支持的音频格式

        Args:
            file_path: 文件路径

        Returns:
            是否为支持的音频文件
        """
        return Path(file_path).suffix.lower() in self.supported_formats


# 便捷函数
_scanner = None


def scan_directory(folder_path: str, recursive: bool = True) -> List[AudioFile]:
    """
    扫描目录的便捷函数

    Args:
        folder_path: 要扫描的文件夹路径
        recursive: 是否递归扫描子文件夹

    Returns:
        音频文件列表
    """
    global _scanner
    if _scanner is None:
        _scanner = AudioScanner()
    return _scanner.scan(folder_path, recursive)
