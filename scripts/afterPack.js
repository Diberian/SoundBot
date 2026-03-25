const fs = require('fs');
const path = require('path');

exports.default = async function(context) {
  const { electronPlatformName, appOutDir } = context;
  
  console.log(`[afterPack] Platform: ${electronPlatformName}`);
  console.log(`[afterPack] App output dir: ${appOutDir}`);
  
  // 后端源目录
  const backendSourceDir = path.join(process.cwd(), 'dist', 'backend', 'soundbot-backend');
  
  // 目标目录（根据平台不同）
  let backendTargetDir;
  if (electronPlatformName === 'win32') {
    backendTargetDir = path.join(appOutDir, 'backend');
  } else if (electronPlatformName === 'darwin') {
    backendTargetDir = path.join(appOutDir, 'SoundBot.app', 'Contents', 'Resources', 'backend');
  } else {
    backendTargetDir = path.join(appOutDir, 'backend');
  }
  
  console.log(`[afterPack] Backend source: ${backendSourceDir}`);
  console.log(`[afterPack] Backend target: ${backendTargetDir}`);
  
  // 检查源目录是否存在
  if (!fs.existsSync(backendSourceDir)) {
    console.error(`[afterPack] ERROR: Backend source directory does not exist: ${backendSourceDir}`);
    throw new Error(`Backend source directory does not exist: ${backendSourceDir}`);
  }
  
  // 创建目标目录
  if (!fs.existsSync(backendTargetDir)) {
    fs.mkdirSync(backendTargetDir, { recursive: true });
    console.log(`[afterPack] Created target directory: ${backendTargetDir}`);
  }
  
  // 复制后端文件
  console.log(`[afterPack] Copying backend files...`);
  copyRecursive(backendSourceDir, backendTargetDir);
  
  // 验证复制结果
  const targetSize = getDirectorySize(backendTargetDir);
  console.log(`[afterPack] Backend copied successfully. Size: ${(targetSize / 1024 / 1024).toFixed(1)} MB`);
  
  if (targetSize < 500 * 1024 * 1024) {
    console.error(`[afterPack] ERROR: Backend size is too small: ${(targetSize / 1024 / 1024).toFixed(1)} MB`);
    throw new Error(`Backend size is too small: ${(targetSize / 1024 / 1024).toFixed(1)} MB`);
  }
  
  console.log('[afterPack] Done!');
};

function copyRecursive(src, dest) {
  const stats = fs.statSync(src);
  
  if (stats.isDirectory()) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    
    const entries = fs.readdirSync(src);
    for (const entry of entries) {
      const srcPath = path.join(src, entry);
      const destPath = path.join(dest, entry);
      copyRecursive(srcPath, destPath);
    }
  } else {
    fs.copyFileSync(src, dest);
  }
}

function getDirectorySize(dir) {
  let size = 0;
  const entries = fs.readdirSync(dir);
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry);
    const stats = fs.statSync(fullPath);
    
    if (stats.isDirectory()) {
      size += getDirectorySize(fullPath);
    } else {
      size += stats.size;
    }
  }
  
  return size;
}
