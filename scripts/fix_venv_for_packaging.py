#!/usr/bin/env python3
"""
修复 venv 中的符号链接，使其可以在打包后使用
"""

import os
import sys
import shutil
from pathlib import Path

def fix_venv_symlinks():
    """修复 venv 中的 Python 解释器符号链接"""
    
    backend_dir = Path(__file__).parent.parent / "backend"
    venv_bin = backend_dir / "venv" / "bin"
    
    print("=" * 60)
    print("修复 venv 符号链接")
    print("=" * 60)
    
    if not venv_bin.exists():
        print(f"❌ venv/bin 目录不存在: {venv_bin}")
        return False
    
    # 找到实际的 Python 解释器
    python_targets = ["python3.12", "python3.11", "python3.10", "python3.9", "python3"]
    actual_python = None
    
    for target in python_targets:
        python_link = venv_bin / target
        if python_link.exists():
            if python_link.is_symlink():
                actual_path = os.readlink(python_link)
                print(f"找到符号链接: {target} -> {actual_path}")
                
                # 如果指向系统路径，需要复制实际文件
                if actual_path.startswith("/opt/") or actual_path.startswith("/usr/"):
                    actual_python = Path(actual_path)
                    break
            else:
                # 已经是实际文件
                print(f"✅ {target} 已经是实际文件")
                actual_python = python_link
                break
    
    if not actual_python or not actual_python.exists():
        print("❌ 无法找到实际的 Python 解释器")
        return False
    
    print(f"\n实际 Python 路径: {actual_python}")
    
    # 复制 Python 解释器到 venv
    venv_python = venv_bin / "python3.12"
    
    # 删除符号链接
    for link_name in ["python", "python3", "python3.12"]:
        link_path = venv_bin / link_name
        if link_path.exists() or link_path.is_symlink():
            print(f"删除: {link_path}")
            link_path.unlink()
    
    # 复制实际的 Python 解释器
    print(f"\n复制 Python 解释器...")
    shutil.copy2(actual_python, venv_python)
    
    # 创建相对符号链接
    os.chdir(venv_bin)
    os.symlink("python3.12", "python3")
    os.symlink("python3.12", "python")
    
    print(f"✅ 已创建新的符号链接")
    
    # 验证
    print("\n验证结果:")
    for name in ["python", "python3", "python3.12"]:
        p = venv_bin / name
        if p.exists():
            if p.is_symlink():
                print(f"  {name} -> {os.readlink(p)}")
            else:
                print(f"  {name} (实际文件)")
    
    return True

if __name__ == "__main__":
    success = fix_venv_symlinks()
    sys.exit(0 if success else 1)
