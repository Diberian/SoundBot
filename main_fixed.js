/**
 * SoundBot - AI 音效管理器
 * Copyright (C) 2026 Nagisa_Huckrick (胡杨)
 *
 * 修复版 main.js - 解决 Windows venv 路径检测问题
 */

const { app, BrowserWindow, Menu, ipcMain, dialog, protocol, net, session, Notification, globalShortcut } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, exec } = require('child_process');

// 自定义协议：用于在渲染进程中安全加载本地音频（避免 file:// 跨源限制）
const AUDIO_PROTOCOL = 'soundmind-audio';

// 必须在 app.ready 之前调用
protocol.registerSchemesAsPrivileged([
  { scheme: AUDIO_PROTOCOL, privileges: { standard: true, secure: true, supportFetchAPI: true } }
]);

let mainWindow;
let backendProcess = null;
const BACKEND_PORT = 8000;
const API_BASE_URL = `http://127.0.0.1:${BACKEND_PORT}/api/v1`;

// 资源下载配置
const DOWNLOAD_CONFIG = {
  githubRepo: 'Huckrick/SoundBot',
  resources: {
    models: { filename: 'models.zip', required: true },
    venvMacos: { filename: 'venv-macos.zip', required: false, platform: 'darwin' },
    venvWindows: { filename: 'venv-windows.zip', required: false, platform: 'win32' }
  }
};

// ==================== 路径辅助函数（修复版） ====================

/**
 * 获取应用资源路径
 * 开发环境：项目根目录
 * 生产环境：app.asar 解压后的资源目录
 */
function getAppPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'app.asar.unpacked');
  }
  return __dirname;
}

/**
 * 获取应用根目录（用户数据目录）
 * 这是存放模型和 venv 的外部目录
 */
function getAppRootDir() {
  if (app.isPackaged) {
    return path.dirname(process.execPath);
  }
  return __dirname;
}

/**
 * 获取后端路径
 * 修复：增加更多 Windows 路径候选
 */
function getBackendPath() {
  const possiblePaths = [
    path.join(getAppRootDir(), 'backend'),
    path.join(__dirname, 'backend'),
    path.join(process.resourcesPath, 'backend'),
    path.join(process.resourcesPath, 'app', 'backend'),
    path.join(process.resourcesPath, 'app.asar.unpacked', 'backend'),
  ];

  for (const p of possiblePaths) {
    const mainPy = path.join(p, 'main.py');
    console.log(`[Backend] 检查路径: ${p}, main.py 存在: ${fs.existsSync(mainPy)}`);
    if (fs.existsSync(mainPy)) {
      console.log(`[Backend] 找到后端路径: ${p}`);
      return p;
    }
  }

  console.log(`[Backend] 警告: 未找到后端路径，使用默认值: ${possiblePaths[0]}`);
  return possiblePaths[0];
}

/**
 * 获取模型路径
 * 修复：增加目录存在性检查，不只是检查 clap 子目录
 */
function getModelsPath() {
  const possiblePaths = [
    path.join(getAppRootDir(), 'models'),
    path.join(__dirname, 'models'),
    path.join(process.resourcesPath, 'models'),
    path.join(process.resourcesPath, 'app', 'models'),
  ];

  for (const p of possiblePaths) {
    // 检查 models 目录本身是否存在
    if (fs.existsSync(p)) {
      console.log(`[Backend] 找到模型路径: ${p}`);
      return p;
    }
  }

  console.log(`[Backend] 警告: 未找到模型路径，使用默认外部路径: ${possiblePaths[0]}`);
  return possiblePaths[0];
}

/**
 * 获取 venv 路径（修复版）
 * 修复：增加更多 Windows 路径候选，改进检测逻辑
 */
function getVenvPath() {
  const isWin = process.platform === 'win32';
  const pythonExe = isWin ? 'Scripts\\python.exe' : 'bin/python';
  const pythonExeAlt = isWin ? 'Scripts\\python3.exe' : 'bin/python3';
  
  const backendPath = getBackendPath();
  
  // 构建可能的路径列表（按优先级排序）
  const possiblePaths = [
    // 1. 应用根目录下的 backend/venv（推荐位置）
    path.join(getAppRootDir(), 'backend', 'venv'),
    // 2. 后端目录下的 venv
    path.join(backendPath, 'venv'),
    // 3. Windows 特殊：用户数据目录
    isWin ? path.join(process.env.LOCALAPPDATA || '', 'SoundBot', 'backend', 'venv') : null,
    // 4. Windows 特殊：应用安装目录
    isWin ? path.join(process.env.PROGRAMFILES || '', 'SoundBot', 'backend', 'venv') : null,
  ].filter(Boolean); // 过滤掉 null

  console.log(`[Backend] 检测 venv 路径 (${isWin ? 'Windows' : 'Unix'})...`);
  
  for (const p of possiblePaths) {
    const pythonPath = path.join(p, pythonExe);
    const pythonPathAlt = path.join(p, pythonExeAlt);
    
    console.log(`[Backend] 检查: ${p}`);
    console.log(`[Backend]   - ${pythonExe}: ${fs.existsSync(pythonPath)}`);
    
    if (fs.existsSync(pythonPath)) {
      console.log(`[Backend] ✓ 找到 venv 路径: ${p}`);
      return p;
    }
    if (fs.existsSync(pythonPathAlt)) {
      console.log(`[Backend] ✓ 找到 venv 路径 (alt): ${p}`);
      return p;
    }
  }

  console.error(`[Backend] ✗ 未找到 venv，已检查路径:`);
  possiblePaths.forEach(p => console.error(`[Backend]   - ${p}`));
  
  // 返回第一个路径（即使不存在，让后续报错更明显）
  return possiblePaths[0];
}

/**
 * 检查资源是否已下载（修复版）
 * 修复：更详细的检查，分别显示 models 和 clap 子目录状态
 */
function checkResources() {
  const modelsPath = getModelsPath();
  const venvPath = getVenvPath();
  
  // 检查 models 目录
  const modelsDirExists = fs.existsSync(modelsPath);
  const clapDirExists = modelsDirExists && fs.existsSync(path.join(modelsPath, 'clap'));
  const modelsExist = modelsDirExists && clapDirExists;
  
  // 检查 venv
  const isWin = process.platform === 'win32';
  const pythonPath = path.join(venvPath, isWin ? 'Scripts\\python.exe' : 'bin/python');
  const venvExist = fs.existsSync(pythonPath);
  
  console.log('[Backend] 资源检查详情:');
  console.log(`[Backend]   models 目录: ${modelsDirExists} (${modelsPath})`);
  console.log(`[Backend]   clap 子目录: ${clapDirExists}`);
  console.log(`[Backend]   venv 路径: ${venvPath}`);
  console.log(`[Backend]   Python 解释器: ${venvExist} (${pythonPath})`);
  
  return {
    models: modelsExist,
    modelsDirExists,
    clapDirExists,
    venv: venvExist,
    modelsPath,
    venvPath,
    pythonPath,
    ready: modelsExist && venvExist
  };
}

/**
 * 显示资源缺失对话框（修复版）
 * 修复：显示更详细的路径信息
 */
async function showResourceMissingDialog(missing) {
  const missingItems = [];
  if (!missing.models) missingItems.push('AI 模型文件');
  if (!missing.venv) missingItems.push('Python 虚拟环境');
  
  const isWin = process.platform === 'win32';
  
  const result = await dialog.showMessageBox(mainWindow, {
    type: 'warning',
    title: '缺少必要资源',
    message: `缺少以下资源:\n${missingItems.join('\n')}`,
    detail: `请从 GitHub Releases 下载以下文件并解压到正确位置:\n\n` +
            `1. models.zip → 解压到:\n   ${getModelsPath()}\n\n` +
            `2. venv-${isWin ? 'windows' : 'macos'}.zip → 解压到:\n   ${path.join(getBackendPath(), 'venv')}\n\n` +
            `注意：解压后应该包含以下结构:\n` +
            `  models/clap/\n` +
            `  backend/venv/${isWin ? 'Scripts/python.exe' : 'bin/python'}`,
    buttons: ['打开下载页面', '稍后手动下载'],
    defaultId: 0,
    cancelId: 1
  });
  
  if (result.response === 0) {
    const { shell } = require('electron');
    shell.openExternal(`https://github.com/${DOWNLOAD_CONFIG.githubRepo}/releases`);
  }
  
  return result.response;
}

// ==================== 后端启动（修复版）====================

/**
 * 启动后端服务器（修复版）
 * 修复：改进 Python 解释器检测，增加 Windows 支持
 */
async function startBackendServer() {
  if (backendProcess) {
    return { success: true, message: '后端服务已在运行' };
  }

  // 检查资源是否就绪
  const resources = checkResources();
  
  if (!resources.ready) {
    console.warn('[Backend] 资源未就绪:', resources);
    await showResourceMissingDialog(resources);
    return { 
      success: false, 
      error: '缺少必要资源',
      details: resources
    };
  }

  const maxRetries = 3;
  let lastError = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`[Backend] 启动尝试 ${attempt}/${maxRetries}...`);

      const backendPath = getBackendPath();
      const mainPy = path.join(backendPath, 'main.py');
      const modelsPath = getModelsPath();
      const venvPath = getVenvPath();

      console.log(`[Backend] 后端路径: ${backendPath}`);
      console.log(`[Backend] 模型路径: ${modelsPath}`);
      console.log(`[Backend] venv路径: ${venvPath}`);

      if (!fs.existsSync(mainPy)) {
        console.error('[Backend] 错误: main.py 不存在');
        return { success: false, error: '后端文件不存在' };
      }

      // 清理残留进程
      if (backendProcess) {
        try {
          backendProcess.kill('SIGTERM');
          await new Promise(r => setTimeout(r, 500));
        } catch (e) {}
        backendProcess = null;
      }

      // 准备环境变量
      const envVars = {
        ...process.env,
        PYTHONUNBUFFERED: '1',
        SOUNDBOT_MODELS_PATH: modelsPath
      };

      // 修复：改进 Python 解释器检测
      const isWin = process.platform === 'win32';
      let pythonCmd = null;
      
      // 候选 Python 路径（按优先级）
      const pythonCandidates = isWin ? [
        path.join(venvPath, 'Scripts', 'python.exe'),
        path.join(venvPath, 'Scripts', 'python3.exe'),
        'python',
        'python3'
      ] : [
        path.join(venvPath, 'bin', 'python'),
        path.join(venvPath, 'bin', 'python3'),
        'python3',
        'python'
      ];
      
      for (const cmd of pythonCandidates) {
        // 对于绝对路径，检查文件是否存在；对于命令，直接尝试
        if (path.isAbsolute(cmd)) {
          if (fs.existsSync(cmd)) {
            pythonCmd = cmd;
            break;
          }
        } else {
          // 系统命令，后续通过 spawn 验证
          pythonCmd = cmd;
          break;
        }
      }

      if (!pythonCmd) {
        return { 
          success: false, 
          error: '未找到 Python 解释器，请检查 venv 是否正确安装' 
        };
      }

      console.log(`[Backend] 使用 Python: ${pythonCmd}`);

      // 启动后端进程
      console.log(`[Backend] 启动: ${pythonCmd} ${mainPy}`);
      console.log(`[Backend] 工作目录: ${backendPath}`);
      
      backendProcess = spawn(pythonCmd, [mainPy], {
        cwd: backendPath,
        env: envVars,
        stdio: ['pipe', 'pipe', 'pipe'],
        windowsHide: true  // Windows 下隐藏控制台窗口
      });

      // 收集启动日志
      let startupOutput = '';
      let errorOutput = '';
      let isStarting = true;

      backendProcess.stdout.on('data', (data) => {
        try {
          const text = data.toString();
          startupOutput += text;
          if (isStarting && backendProcess) {
            console.log('[Backend]', text.trim());
          }
        } catch (e) {}
      });

      backendProcess.stderr.on('data', (data) => {
        try {
          const text = data.toString();
          errorOutput += text;
          if (isStarting && backendProcess) {
            console.error('[Backend Error]', text.trim());
          }
        } catch (e) {}
      });

      backendProcess.on('error', (error) => {
        console.error('[Backend] 进程启动失败:', error);
        lastError = error;
        backendProcess = null;
      });

      backendProcess.on('exit', (code, signal) => {
        console.log(`[Backend] 进程退出，代码: ${code}, 信号: ${signal}`);
        if (code !== 0 && code !== null) {
          console.error(`[Backend] 非正常退出`);
          console.error(`[Backend] 输出: ${startupOutput.slice(-2000)}`);  // 最后 2000 字符
          console.error(`[Backend] 错误: ${errorOutput.slice(-2000)}`);
        }
        backendProcess = null;
      });

      // 等待服务启动
      await new Promise((resolve, reject) => {
        let retries = 0;
        // 修复：Windows 下延长超时时间
        const maxHealthChecks = isWin ? 60 : 30;

        const checkServer = setInterval(async () => {
          try {
            const healthResponse = await fetch(`${API_BASE_URL}/health`);
            if (!healthResponse.ok) {
              throw new Error(`健康检查失败: ${healthResponse.status}`);
            }

            const modelResponse = await fetch(`${API_BASE_URL}/model/status`);
            if (modelResponse.ok) {
              const modelStatus = await modelResponse.json();
              const isLoaded = modelStatus.model_status?.loaded || modelStatus.loaded;
              
              if (isLoaded) {
                clearInterval(checkServer);
                isStarting = false;
                console.log('[Backend] 服务启动完成，模型已加载');
                resolve();
              } else {
                console.log(`[Backend] 模型加载中... (${retries}/${maxHealthChecks})`);
              }
            }
          } catch (err) {
            retries++;
            console.log(`[Backend] 等待服务启动... (${retries}/${maxHealthChecks})`);
            if (retries >= maxHealthChecks) {
              clearInterval(checkServer);
              reject(new Error(
                `服务启动超时 (${maxHealthChecks}秒)\n` +
                `可能原因：\n` +
                `1. Python 依赖缺失\n` +
                `2. 模型加载时间过长（Windows 机械硬盘可能需要更久）\n` +
                `3. 端口 8000 被占用\n\n` +
                `启动输出:\n${startupOutput.slice(-1000)}\n\n` +
                `错误输出:\n${errorOutput.slice(-1000)}`
              ));
            }
          }
        }, 1000);
      });

      console.log(`[Backend] 第 ${attempt} 次尝试成功启动`);
      return { success: true, message: '后端服务已启动' };

    } catch (error) {
      lastError = error;
      console.error(`[Backend] 第 ${attempt} 次启动失败:`, error.message);

      if (attempt < maxRetries) {
        console.log('[Backend] 等待 2 秒后重试...');
        if (backendProcess) {
          try {
            backendProcess.kill('SIGKILL');
          } catch (e) {}
          backendProcess = null;
        }
        await new Promise(r => setTimeout(r, 2000));
      }
    }
  }

  return {
    success: false,
    error: `后端服务启动失败，已尝试 ${maxRetries} 次\n最后错误: ${lastError?.message || '未知错误'}\n\n请检查：\n1. Python 依赖是否已安装\n2. 端口 8000 是否被占用\n3. 查看详细日志：%APPDATA%\\SoundBot\\logs\\`
  };
}

// 停止后端服务器
async function stopBackendServer() {
  if (!backendProcess) {
    return { success: true, message: '后端服务未在运行' };
  }

  return new Promise((resolve) => {
    backendProcess.once('exit', () => {
      backendProcess = null;
      resolve({ success: true, message: '后端服务已停止' });
    });

    backendProcess.kill('SIGTERM');
    setTimeout(() => {
      if (backendProcess) {
        backendProcess.kill('SIGKILL');
      }
      resolve({ success: true, message: '后端服务已强制停止' });
    }, 5000);
  });
}

// ==================== 窗口创建 ====================

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1400,
    minHeight: 900,
    title: 'SoundBot - AI 音效管理器',
    icon: path.join(__dirname, 'assets/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true,
      allowRunningInsecureContent: false
    },
    titleBarStyle: 'default',
    show: false,
    backgroundColor: '#0a0a0a'
  });

  // 设置 CSP
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self'; " +
          "script-src 'self' 'unsafe-inline' https://unpkg.com; " +
          "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
          "font-src 'self' https://fonts.gstatic.com; " +
          "img-src 'self' data: blob:; " +
          "media-src 'self' blob: soundmind-audio:; " +
          "connect-src 'self' http://127.0.0.1:8000 ws://127.0.0.1:8000 " +
          "https://api.openai.com https://api.moonshot.cn https://api.anthropic.com " +
          "https://api.deepseek.com https://api.siliconflow.cn " +
          "https://generativelanguage.googleapis.com https://*.openai.azure.com " +
          "https://api.kimi.com;"
        ]
      }
    });
  });

  const indexPath = path.join(__dirname, 'index.html');
  mainWindow.loadFile(indexPath);

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (process.argv.includes('--dev')) {
      mainWindow.webContents.openDevTools();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  createMenu();
  setupIpcHandlers();
}

function createMenu() {
  const template = [
    {
      label: '文件',
      submenu: [
        {
          label: '新建项目',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.send('menu-new-project');
          }
        },
        {
          label: '导入文件',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            mainWindow.webContents.send('menu-import-file');
          }
        },
        { type: 'separator' },
        {
          label: '退出',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: '编辑',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' }
      ]
    },
    {
      label: '视图',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools', accelerator: 'F12' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: '窗口',
      submenu: [
        { role: 'minimize' },
        { role: 'close' }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// ==================== IPC 处理（修复版）====================

function setupIpcHandlers() {
  ipcMain.handle('window-control', (event, action) => {
    switch (action) {
      case 'minimize':
        mainWindow.minimize();
        break;
      case 'maximize':
        if (mainWindow.isMaximized()) {
          mainWindow.unmaximize();
        } else {
          mainWindow.maximize();
        }
        break;
      case 'close':
        mainWindow.close();
        break;
      case 'isMaximized':
        return mainWindow.isMaximized();
    }
  });

  ipcMain.handle('file-import', async (event, action, data) => {
    console.log('[IPC] file-import 收到请求:', action, data);
    try {
      switch (action) {
        case 'select-audio': {
          const result = await dialog.showOpenDialog(mainWindow, {
            title: '选择音频文件',
            filters: [
              { name: '音频文件', extensions: ['wav', 'mp3', 'aac', 'flac', 'ogg', 'm4a'] },
              { name: '所有文件', extensions: ['*'] }
            ],
            properties: ['openFile', 'multiSelections']
          });

          if (!result.canceled && result.filePaths.length > 0) {
            const fileInfo = await Promise.all(
              result.filePaths.map(async (filePath) => {
                const stats = fs.statSync(filePath);
                return {
                  path: filePath,
                  name: path.basename(filePath),
                  size: stats.size,
                  type: path.extname(filePath).toLowerCase(),
                  lastModified: stats.mtime
                };
              })
            );
            mainWindow.webContents.send('files-selected', fileInfo);
            return { success: true, files: fileInfo };
          }
          return { success: false, canceled: true };
        }

        case 'select-folder': {
          const result = await dialog.showOpenDialog(mainWindow, {
            title: '选择文件夹',
            properties: ['openDirectory']
          });

          if (!result.canceled && result.filePaths.length > 0) {
            return { success: true, folder: result.filePaths[0] };
          }
          return { success: false, canceled: true };
        }

        case 'validate-type': {
          const supportedTypes = ['.wav', '.mp3', '.aac', '.flac', '.ogg', '.m4a'];
          const ext = path.extname(data).toLowerCase();
          return { success: supportedTypes.includes(ext), type: ext };
        }

        default:
          return { success: false, error: '未知操作' };
      }
    } catch (error) {
      console.error('文件导入错误:', error);
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('read-audio-file', async (event, filePath) => {
    try {
      if (!filePath || !path.isAbsolute(filePath)) {
        return { success: false, error: '无效的文件路径' };
      }
      if (!fs.existsSync(filePath)) {
        return { success: false, error: '文件不存在' };
      }
      const buffer = fs.readFileSync(filePath);
      const arrayBuffer = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
      return { success: true, data: Array.from(new Uint8Array(arrayBuffer)) };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  ipcMain.handle('start-drag', async (event, filePath) => {
    try {
      if (!filePath || !fs.existsSync(filePath)) {
        return { success: false, error: '文件不存在' };
      }
      const iconPath = path.join(__dirname, 'assets', 'audio-icon.png');
      const finalIconPath = fs.existsSync(iconPath) ? iconPath : undefined;

      mainWindow.webContents.startDrag({
        file: filePath,
        icon: finalIconPath
      });
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });

  // 后端 API 处理
  ipcMain.handle('backend-api', async (event, action, data) => {
    try {
      switch (action) {
        case 'health': {
          const response = await fetch(`${API_BASE_URL}/health`);
          return await response.json();
        }

        case 'scan': {
          const response = await fetch(`${API_BASE_URL}/scan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              folder_path: data.folderPath,
              recursive: data.recursive
            })
          });
          return await response.json();
        }

        case 'search': {
          const response = await fetch(`${API_BASE_URL}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query: data.query,
              top_k: data.topK,
              threshold: data.threshold,
              page: data.page || 1,
              page_size: data.page_size || 50
            })
          });
          return await response.json();
        }

        case 'start-server': {
          return await startBackendServer();
        }

        case 'stop-server': {
          return await stopBackendServer();
        }

        case 'check-resources': {
          const resources = checkResources();
          return { 
            success: true, 
            resources: resources,
            downloadUrl: `https://github.com/${DOWNLOAD_CONFIG.githubRepo}/releases`
          };
        }

        default:
          return { success: false, error: '未知操作' };
      }
    } catch (error) {
      console.error('后端 API 错误:', error);
      return { success: false, error: error.message };
    }
  });
}

// ==================== 应用生命周期 ====================

app.whenReady().then(async () => {
  // 注册自定义协议
  const defaultSession = session.defaultSession;
  
  defaultSession.protocol.handle(AUDIO_PROTOCOL, (request) => {
    try {
      const u = new URL(request.url);
      let filePath = decodeURIComponent(u.pathname);
      
      if (!filePath || !path.isAbsolute(filePath)) {
        return new Response('Invalid path', { status: 400 });
      }
      return net.fetch('file://' + filePath);
    } catch (e) {
      return new Response('Error', { status: 500 });
    }
  });

  createWindow();
  
  // 自动启动后端服务
  try {
    const result = await startBackendServer();
    if (result.success) {
      console.log('后端服务启动成功');
    } else {
      console.warn('后端服务启动失败:', result.error);
    }
  } catch (error) {
    console.error('启动后端服务时出错:', error);
  }
});

app.on('window-all-closed', async () => {
  if (process.platform !== 'darwin') {
    if (backendProcess) {
      await stopBackendServer();
    }
    app.quit();
  }
});

app.on('activate', async () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
    if (!backendProcess) {
      try {
        await startBackendServer();
      } catch (error) {
        console.error('重新启动后端失败:', error);
      }
    }
  }
});

app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    console.log('Blocked new window to:', navigationUrl);
  });
});
