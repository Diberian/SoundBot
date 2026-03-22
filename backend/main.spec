# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SoundBot backend (lightweight version)
Excludes large dependencies (torch, transformers) - they are provided via venv
"""

import sys
import os
from pathlib import Path

block_cipher = None

# 获取项目根目录
spec_dir = Path(os.getcwd())
backend_dir = spec_dir
project_root = backend_dir.parent

# 添加数据文件（只包含代码，不包含大依赖）
datas = []

# 添加 core 目录
if (backend_dir / 'core').exists():
    datas.append((str(backend_dir / 'core'), 'core'))

# 添加 utils 目录
if (backend_dir / 'utils').exists():
    datas.append((str(backend_dir / 'utils'), 'utils'))

# 添加配置文件
if (backend_dir / 'config.py').exists():
    datas.append((str(backend_dir / 'config.py'), '.'))

# 添加其他 Python 文件
for py_file in ['database.py', 'reindex_folder.py', 'reset_and_reindex.py']:
    if (backend_dir / py_file).exists():
        datas.append((str(backend_dir / py_file), '.'))

# 隐藏导入（只包含轻量级依赖）
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'fastapi.middleware.cors',
    'chromadb',
    'chromadb.config',
    'pydantic',
    'pydantic_settings',
    # 注意：torch, transformers, numpy 等大依赖通过 venv 提供
]

# 排除大依赖（这些将通过 venv 提供）
excludes = [
    'torch',
    'torchaudio',
    'transformers',
    'numpy',
    'scipy',
    'pandas',
    'matplotlib',
    'PIL',
    'cv2',
]

a = Analysis(
    [str(backend_dir / 'main.py')],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SoundBot-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
