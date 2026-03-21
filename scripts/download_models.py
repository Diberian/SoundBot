#!/usr/bin/env python3
"""
下载 AI 模型脚本
用于 CI/CD 或首次设置时下载模型文件
"""

import os
import sys
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

def download_clap_model():
    """下载 CLAP 模型到本地 models 目录"""
    from transformers import ClapModel, ClapProcessor
    
    model_name = "laion/larger_clap_general"
    models_dir = Path(__file__).parent.parent / "models" / "clap"
    
    print(f"正在下载 CLAP 模型到 {models_dir}...")
    print(f"模型: {model_name}")
    
    # 下载模型和处理器
    model = ClapModel.from_pretrained(model_name)
    processor = ClapProcessor.from_pretrained(model_name)
    
    # 保存到本地
    models_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(models_dir)
    processor.save_pretrained(models_dir)
    
    print(f"✅ 模型下载完成！")
    print(f"📦 模型大小: {sum(f.stat().st_size for f in models_dir.rglob('*') if f.is_file()) / 1024 / 1024:.1f} MB")
    
    return models_dir

if __name__ == "__main__":
    try:
        download_clap_model()
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        sys.exit(1)
