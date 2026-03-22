#!/usr/bin/env python3
"""
SoundBot 资源下载管理器
用于从 GitHub Releases 下载模型和 Python 环境
"""

import os
import sys
import json
import hashlib
import zipfile
import shutil
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import ssl

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 默认配置
DEFAULT_CONFIG = {
    "github_repo": "Huckrick/SoundBot",
    "resources": {
        "models": {
            "filename": "models.zip",
            "extract_to": "models",
            "required": True,
            "description": "AI 模型文件 (CLAP等)"
        },
        "venv_macos": {
            "filename": "venv-macos.zip",
            "extract_to": "backend/venv",
            "required": False,
            "platform": "darwin",
            "description": "macOS Python 虚拟环境"
        },
        "venv_windows": {
            "filename": "venv-windows.zip",
            "extract_to": "backend/venv",
            "required": False,
            "platform": "win32",
            "description": "Windows Python 虚拟环境"
        }
    }
}

CONFIG_FILE = "download_config.json"


def get_config():
    """获取下载配置"""
    config_path = Path(__file__).parent.parent / CONFIG_FILE
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG


def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent.parent


def get_platform():
    """获取当前平台"""
    if sys.platform == 'darwin':
        return 'darwin'
    elif sys.platform == 'win32':
        return 'win32'
    else:
        return 'linux'


def get_download_dir():
    """获取下载目录"""
    download_dir = get_project_root() / "downloads"
    download_dir.mkdir(exist_ok=True)
    return download_dir


def get_github_releases(repo):
    """获取 GitHub Releases 列表"""
    url = f"https://api.github.com/repos/{repo}/releases"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "SoundBot-DownloadManager/1.0"
    }
    
    try:
        ctx = ssl.create_default_context()
        req = Request(url, headers=headers)
        with urlopen(req, context=ctx, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[ERROR] 获取 releases 失败: {e}")
        return None


def get_latest_release(repo):
    """获取最新 release"""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "SoundBot-DownloadManager/1.0"
    }
    
    try:
        ctx = ssl.create_default_context()
        req = Request(url, headers=headers)
        with urlopen(req, context=ctx, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[ERROR] 获取最新 release 失败: {e}")
        return None


def download_file(url, dest_path, progress_callback=None):
    """下载文件并显示进度"""
    try:
        ctx = ssl.create_default_context()
        req = Request(url, headers={"User-Agent": "SoundBot-DownloadManager/1.0"})
        
        with urlopen(req, context=ctx, timeout=60) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            block_size = 8192
            
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        progress_callback(downloaded, total_size, progress)
        
        return True
    except Exception as e:
        print(f"[ERROR] 下载失败: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False


def extract_zip(zip_path, extract_to, progress_callback=None):
    """解压 zip 文件"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            total_files = len(zip_ref.namelist())
            
            for i, file in enumerate(zip_ref.namelist()):
                zip_ref.extract(file, extract_to)
                if progress_callback:
                    progress = ((i + 1) / total_files) * 100
                    progress_callback(i + 1, total_files, progress)
        
        return True
    except Exception as e:
        print(f"[ERROR] 解压失败: {e}")
        return False


def verify_download(file_path, expected_hash=None):
    """验证下载的文件"""
    if not os.path.exists(file_path):
        return False
    
    if expected_hash:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        actual_hash = sha256_hash.hexdigest()
        if actual_hash != expected_hash:
            print(f"[ERROR] 文件校验失败: {actual_hash} != {expected_hash}")
            return False
    
    return True


def download_resource(resource_type, release_tag=None, force=False):
    """
    下载指定资源
    
    Args:
        resource_type: 'models', 'venv_macos', 'venv_windows'
        release_tag: 指定 release 标签，None 表示最新版
        force: 是否强制重新下载
    """
    config = get_config()
    repo = config.get("github_repo", DEFAULT_CONFIG["github_repo"])
    
    if resource_type not in config.get("resources", {}):
        print(f"[ERROR] 未知资源类型: {resource_type}")
        return False
    
    resource = config["resources"][resource_type]
    
    # 检查平台要求
    if "platform" in resource:
        if resource["platform"] != get_platform():
            print(f"[INFO] 跳过 {resource_type}: 不适用于当前平台")
            return True
    
    # 获取 release 信息
    if release_tag:
        releases = get_github_releases(repo)
        if not releases:
            print("[ERROR] 无法获取 releases 列表")
            return False
        
        release = None
        for r in releases:
            if r["tag_name"] == release_tag:
                release = r
                break
        
        if not release:
            print(f"[ERROR] 未找到 release: {release_tag}")
            return False
    else:
        release = get_latest_release(repo)
        if not release:
            print("[ERROR] 无法获取最新 release")
            return False
    
    # 查找资源文件
    filename = resource["filename"]
    asset = None
    for a in release.get("assets", []):
        if a["name"] == filename:
            asset = a
            break
    
    if not asset:
        print(f"[ERROR] 在 release {release['tag_name']} 中未找到 {filename}")
        print(f"[INFO] 可用资源: {[a['name'] for a in release.get('assets', [])]}")
        return False
    
    # 检查是否已存在
    project_root = get_project_root()
    extract_to = project_root / resource["extract_to"]
    
    if extract_to.exists() and not force:
        print(f"[INFO] {resource_type} 已存在: {extract_to}")
        print(f"[INFO] 使用 --force 重新下载")
        return True
    
    # 下载文件
    download_dir = get_download_dir()
    download_path = download_dir / filename
    
    print(f"[INFO] 下载 {resource_type}...")
    print(f"[INFO] 版本: {release['tag_name']}")
    print(f"[INFO] 大小: {asset['size'] / 1024 / 1024:.1f} MB")
    print(f"[INFO] 保存到: {download_path}")
    
    def progress_callback(downloaded, total, percent):
        mb = downloaded / 1024 / 1024
        total_mb = total / 1024 / 1024
        print(f"\r[PROGRESS] {mb:.1f}/{total_mb:.1f} MB ({percent:.1f}%)", end='', flush=True)
    
    if not download_file(asset["browser_download_url"], download_path, progress_callback):
        print()
        return False
    
    print()
    print(f"[OK] 下载完成: {download_path}")
    
    # 解压文件
    print(f"[INFO] 解压到: {extract_to}")
    
    # 清理旧文件
    if extract_to.exists():
        print(f"[INFO] 清理旧文件...")
        shutil.rmtree(extract_to)
    
    extract_to.parent.mkdir(parents=True, exist_ok=True)
    
    def extract_progress(current, total, percent):
        print(f"\r[PROGRESS] 解压中... {current}/{total} ({percent:.1f}%)", end='', flush=True)
    
    if not extract_zip(download_path, extract_to.parent, extract_progress):
        print()
        return False
    
    print()
    print(f"[OK] 解压完成: {extract_to}")
    
    # 清理下载文件
    if download_path.exists():
        download_path.unlink()
        print(f"[INFO] 清理临时文件")
    
    return True


def check_resources():
    """检查所需资源是否已下载"""
    config = get_config()
    project_root = get_project_root()
    
    results = {}
    all_ready = True
    
    print("=" * 60)
    print("资源检查")
    print("=" * 60)
    
    for resource_type, resource in config.get("resources", {}).items():
        # 跳过不适用当前平台的资源
        if "platform" in resource:
            if resource["platform"] != get_platform():
                continue
        
        extract_to = project_root / resource["extract_to"]
        exists = extract_to.exists()
        required = resource.get("required", False)
        
        status = "✓" if exists else "✗"
        req_mark = "[必需]" if required else "[可选]"
        
        print(f"{status} {resource_type} {req_mark}: {extract_to}")
        
        results[resource_type] = {
            "exists": exists,
            "required": required,
            "path": str(extract_to)
        }
        
        if required and not exists:
            all_ready = False
    
    print("=" * 60)
    if all_ready:
        print("[OK] 所有必需资源已准备就绪")
    else:
        print("[WARN] 部分必需资源缺失，请运行下载命令")
    
    return results, all_ready


def setup_python_env():
    """设置 Python 环境（如果没有 venv）"""
    project_root = get_project_root()
    venv_path = project_root / "backend" / "venv"
    
    if venv_path.exists():
        print(f"[INFO] Python 环境已存在: {venv_path}")
        return True
    
    print("[INFO] 创建 Python 虚拟环境...")
    
    try:
        backend_path = project_root / "backend"
        backend_path.mkdir(exist_ok=True)
        
        # 创建 venv
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
        print(f"[OK] 虚拟环境创建成功: {venv_path}")
        
        # 安装依赖
        print("[INFO] 安装依赖...")
        requirements = backend_path / "requirements.txt"
        
        if requirements.exists():
            if sys.platform == 'win32':
                pip_cmd = venv_path / "Scripts" / "pip.exe"
            else:
                pip_cmd = venv_path / "bin" / "pip"
            
            subprocess.check_call([str(pip_cmd), "install", "-r", str(requirements)])
            print("[OK] 依赖安装完成")
        
        return True
    except Exception as e:
        print(f"[ERROR] 创建 Python 环境失败: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SoundBot 资源下载管理器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s check              检查资源状态
  %(prog)s download models    下载 AI 模型
  %(prog)s download venv      下载 Python 环境（当前平台）
  %(prog)s download all       下载所有资源
  %(prog)s setup              自动设置环境（下载资源或创建 venv）
        """
    )
    
    parser.add_argument(
        "command",
        choices=["check", "download", "setup"],
        help="要执行的命令"
    )
    
    parser.add_argument(
        "resource",
        nargs="?",
        choices=["models", "venv", "venv_macos", "venv_windows", "all"],
        help="要下载的资源类型"
    )
    
    parser.add_argument(
        "--tag", "-t",
        help="指定 release 标签（默认使用最新版）"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制重新下载"
    )
    
    parser.add_argument(
        "--repo", "-r",
        help="GitHub 仓库地址（格式: owner/repo）"
    )
    
    args = parser.parse_args()
    
    # 更新配置
    if args.repo:
        config = get_config()
        config["github_repo"] = args.repo
        config_path = get_project_root() / CONFIG_FILE
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"[INFO] 已更新仓库配置: {args.repo}")
    
    if args.command == "check":
        check_resources()
    
    elif args.command == "download":
        if not args.resource:
            print("[ERROR] 请指定要下载的资源类型")
            parser.print_help()
            sys.exit(1)
        
        if args.resource == "all":
            resources = ["models"]
            if get_platform() == "darwin":
                resources.append("venv_macos")
            elif get_platform() == "win32":
                resources.append("venv_windows")
            
            success = True
            for res in resources:
                if not download_resource(res, args.tag, args.force):
                    success = False
            
            sys.exit(0 if success else 1)
        
        elif args.resource == "venv":
            if get_platform() == "darwin":
                success = download_resource("venv_macos", args.tag, args.force)
            elif get_platform() == "win32":
                success = download_resource("venv_windows", args.tag, args.force)
            else:
                print("[ERROR] 不支持的平台，尝试创建本地 venv...")
                success = setup_python_env()
            sys.exit(0 if success else 1)
        
        else:
            success = download_resource(args.resource, args.tag, args.force)
            sys.exit(0 if success else 1)
    
    elif args.command == "setup":
        print("=" * 60)
        print("SoundBot 自动设置")
        print("=" * 60)
        
        # 检查资源
        results, all_ready = check_resources()
        
        if all_ready:
            print("\n[OK] 环境已准备就绪，无需操作")
            sys.exit(0)
        
        # 尝试下载缺失的资源
        print("\n[INFO] 开始下载缺失的资源...")
        
        # 下载模型
        if not results.get("models", {}).get("exists", False):
            if not download_resource("models"):
                print("[WARN] 模型下载失败，应用可能无法正常使用")
        
        # 下载或创建 venv
        platform_key = f"venv_{get_platform()}"
        if not results.get(platform_key, {}).get("exists", False):
            if not download_resource(platform_key):
                print("[INFO] 尝试创建本地 Python 环境...")
                setup_python_env()
        
        # 最终检查
        print("\n" + "=" * 60)
        results, all_ready = check_resources()
        sys.exit(0 if all_ready else 1)


if __name__ == "__main__":
    main()
