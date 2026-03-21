#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量添加版权头到项目文件"""

import os

COPYRIGHT_HEADER = '''# -*- coding: utf-8 -*-
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

'''

JS_HEADER = '''/**
 * SoundBot - AI 音效管理器
 * Copyright (C) 2026 Nagisa_Huckrick (胡杨)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

'''

def add_header_to_py_file(filepath):
    """添加版权头到 Python 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, IOError) as e:
        print(f"跳过（无法读取）: {filepath} - {e}")
        return
    
    # 检查是否已经有版权头
    if 'Copyright (C) 2026 Nagisa_Huckrick' in content:
        print(f"跳过（已有版权头）: {filepath}")
        return
    
    # 检查是否有 encoding 声明
    if content.startswith('# -*- coding:'):
        # 替换现有的 encoding 行
        lines = content.split('\n')
        new_lines = [COPYRIGHT_HEADER.rstrip()]
        for line in lines[1:]:
            new_lines.append(line)
        new_content = '\n'.join(new_lines)
    else:
        new_content = COPYRIGHT_HEADER + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"已添加: {filepath}")

def add_header_to_js_file(filepath):
    """添加版权头到 JS 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except (UnicodeDecodeError, IOError) as e:
        print(f"跳过（无法读取）: {filepath} - {e}")
        return
    
    # 检查是否已经有版权头
    if 'Copyright (C) 2026 Nagisa_Huckrick' in content:
        print(f"跳过（已有版权头）: {filepath}")
        return
    
    new_content = JS_HEADER + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"已添加: {filepath}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, 'backend')
    
    # 遍历 backend 目录下的所有 .py 文件（排除 venv 和 db）
    for root, dirs, files in os.walk(backend_dir):
        # 排除 venv 和 db 目录
        dirs[:] = [d for d in dirs if d not in ['venv', 'db', '__pycache__', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                add_header_to_py_file(filepath)
    
    # 处理根目录下的 JS 文件
    js_files = ['preload.js']
    for js_file in js_files:
        filepath = os.path.join(base_dir, js_file)
        if os.path.exists(filepath):
            add_header_to_js_file(filepath)
    
    print("\n版权头添加完成！")

if __name__ == '__main__':
    main()
