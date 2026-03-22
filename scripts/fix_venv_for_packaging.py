#!/usr/bin/env python3
"""
修复 venv 中的硬编码路径，使其可以在打包后使用
支持 macOS、Linux 和 Windows
"""

import os
import sys
import shutil
import re
from pathlib import Path


def fix_venv_for_windows(venv_path: Path):
    """修复 Windows 虚拟环境中的硬编码路径"""
    
    print("=" * 60)
    print("修复 Windows venv 硬编码路径")
    print("=" * 60)
    
    # 1. 修复 pyvenv.cfg
    pyvenv_cfg = venv_path / "pyvenv.cfg"
    if pyvenv_cfg.exists():
        print(f"\n修复: {pyvenv_cfg}")
        with open(pyvenv_cfg, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 获取当前 Python 路径（打包后的路径）
        current_python = sys.executable
        
        # 替换所有绝对路径为相对路径或当前路径
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 如果是路径，尝试修复
                if key in ['home', 'base-prefix', 'base-exec-prefix', 'base-executable']:
                    # 使用相对路径或标记为动态
                    if key == 'home':
                        new_lines.append(f'{key} = python')
                    else:
                        new_lines.append(f'{key} = {current_python}')
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        with open(pyvenv_cfg, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print("✅ pyvenv.cfg 已修复")
    
    # 2. 修复 activate.bat
    activate_bat = venv_path / "Scripts" / "activate.bat"
    if activate_bat.exists():
        print(f"\n修复: {activate_bat}")
        with open(activate_bat, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 替换硬编码路径为动态路径
        content = re.sub(
            r'set "VIRTUAL_ENV=.*"',
            'set "VIRTUAL_ENV=%~dp0.."',
            content
        )
        
        with open(activate_bat, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ activate.bat 已修复")
    
    # 3. 修复 Activate.ps1
    activate_ps1 = venv_path / "Scripts" / "Activate.ps1"
    if activate_ps1.exists():
        print(f"\n修复: {activate_ps1}")
        with open(activate_ps1, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 替换硬编码路径
        content = re.sub(
            r'\$env:VIRTUAL_ENV = ".*"',
            '$env:VIRTUAL_ENV = Split-Path -Parent $PSScriptRoot',
            content
        )
        
        with open(activate_ps1, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Activate.ps1 已修复")
    
    # 4. 修复所有 .exe 文件的 shebang（如果可能）
    scripts_dir = venv_path / "Scripts"
    if scripts_dir.exists():
        print(f"\n检查 Scripts 目录: {scripts_dir}")
        # Windows 的 .exe 文件无法直接修改，需要在运行时处理
    
    print("\n✅ Windows venv 修复完成")
    return True


def fix_venv_for_unix(venv_path: Path):
    """修复 macOS/Linux 虚拟环境中的符号链接"""
    
    print("=" * 60)
    print("修复 Unix venv 符号链接")
    print("=" * 60)
    
    venv_bin = venv_path / "bin"
    
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
                try:
                    actual_path = os.readlink(python_link)
                    print(f"找到符号链接: {target} -> {actual_path}")
                    
                    # 如果指向系统路径，需要记录
                    if actual_path.startswith("/") and not actual_path.startswith(str(venv_path)):
                        actual_python = Path(actual_path)
                        break
                except OSError:
                    continue
            else:
                # 已经是实际文件
                print(f"✅ {target} 已经是实际文件")
                actual_python = python_link
                break
    
    if not actual_python:
        print("⚠️  未找到需要修复的符号链接")
        return True
    
    print(f"\n实际 Python 路径: {actual_python}")
    
    if actual_python.exists():
        # 复制 Python 解释器到 venv
        venv_python = venv_bin / "python3.12"
        
        # 删除符号链接
        for link_name in ["python", "python3", "python3.12"]:
            link_path = venv_bin / link_name
            if link_path.exists() or link_path.is_symlink():
                try:
                    link_path.unlink()
                    print(f"删除: {link_path}")
                except OSError as e:
                    print(f"警告: 无法删除 {link_path}: {e}")
        
        # 复制实际的 Python 解释器
        print(f"\n复制 Python 解释器...")
        try:
            shutil.copy2(actual_python, venv_python)
            
            # 创建相对符号链接
            os.chdir(venv_bin)
            os.symlink("python3.12", "python3")
            os.symlink("python3.12", "python")
            
            print(f"✅ 已创建新的符号链接")
        except Exception as e:
            print(f"❌ 复制失败: {e}")
            return False
    
    # 修复 pyvenv.cfg
    pyvenv_cfg = venv_path / "pyvenv.cfg"
    if pyvenv_cfg.exists():
        print(f"\n修复: {pyvenv_cfg}")
        with open(pyvenv_cfg, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换所有绝对路径为相对路径
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 如果是路径，尝试修复
                if key in ['home', 'base-prefix', 'base-exec-prefix', 'base-executable']:
                    # 使用相对路径
                    new_lines.append(f'{key} = python')
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        with open(pyvenv_cfg, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print("✅ pyvenv.cfg 已修复")
    
    print("\n✅ Unix venv 修复完成")
    return True


def fix_venv_symlinks():
    """主函数：根据平台修复 venv"""
    
    backend_dir = Path(__file__).parent.parent / "backend"
    venv_path = backend_dir / "venv"
    
    if not venv_path.exists():
        print(f"❌ venv 目录不存在: {venv_path}")
        return False
    
    print(f"venv 路径: {venv_path}")
    
    # 根据平台选择修复方法
    if sys.platform == 'win32':
        return fix_venv_for_windows(venv_path)
    else:
        return fix_venv_for_unix(venv_path)


if __name__ == "__main__":
    success = fix_venv_symlinks()
    sys.exit(0 if success else 1)
