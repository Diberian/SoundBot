#!/usr/bin/env python3
"""
使用 PyInstaller 打包 Python 后端为独立可执行文件
这样用户无需安装 Python 即可运行
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_backend():
    """打包后端为可执行文件"""
    
    backend_dir = Path(__file__).parent.parent / "backend"
    dist_dir = Path(__file__).parent.parent / "dist-backend"
    
    print("=" * 60)
    print("SoundBot 后端打包工具")
    print("=" * 60)
    
    # 清理旧的构建
    if dist_dir.exists():
        print(f"清理旧的构建目录: {dist_dir}")
        shutil.rmtree(dist_dir)
    
    # PyInstaller 参数
    main_py = backend_dir / "main.py"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "soundbot-backend",
        "--onefile",  # 打包成单个文件
        "--distpath", str(dist_dir),
        "--workpath", str(dist_dir / "build"),
        "--specpath", str(dist_dir),
        "--clean",
        "--noconfirm",
        # 隐藏导入（根据你的依赖调整）
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        "--hidden-import", "transformers",
        "--hidden-import", "torch",
        "--hidden-import", "numpy",
        "--hidden-import", "chromadb",
        "--hidden-import", "sentence_transformers",
        "--hidden-import", "pydantic",
        "--hidden-import", "starlette",
        # 数据文件
        "--add-data", f"{backend_dir}/core:core",
        "--add-data", f"{backend_dir}/models:models",
        "--add-data", f"{backend_dir}/utils:utils",
        str(main_py)
    ]
    
    print(f"\n执行命令: {' '.join(cmd)}")
    print("\n开始打包...这可能需要几分钟...\n")
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print("❌ 打包失败！")
        return False
    
    # 检查输出
    executable = dist_dir / "soundbot-backend"
    if sys.platform == "win32":
        executable = dist_dir / "soundbot-backend.exe"
    
    if executable.exists():
        size_mb = executable.stat().st_size / 1024 / 1024
        print(f"\n✅ 打包成功！")
        print(f"📦 可执行文件: {executable}")
        print(f"📊 文件大小: {size_mb:.1f} MB")
        return True
    else:
        print("❌ 未找到生成的可执行文件")
        return False

if __name__ == "__main__":
    # 检查 PyInstaller 是否安装
    try:
        import PyInstaller
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    success = build_backend()
    sys.exit(0 if success else 1)
