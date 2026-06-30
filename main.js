const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

let mainWindow = null;
let pythonProcess = null;
const PYTHON_PORT = 8000;
const PYTHON_SCRIPT = 'src.api.main:app';

// Kill any process on port 8000 before starting
function killPortProcess() {
  return new Promise((resolve) => {
    const cmd = process.platform === 'win32'
      ? `netstat -ano | findstr :${PYTHON_PORT}`
      : `lsof -ti :${PYTHON_PORT}`;

    const exec = require('child_process').exec;
    exec(cmd, (error, stdout) => {
      if (!error && stdout.trim()) {
        const pid = process.platform === 'win32'
          ? stdout.split(/\s+/)[4]
          : stdout.trim();

        try {
          process.kill(pid);
          console.log(`Killed process on port ${PYTHON_PORT}: ${pid}`);
        } catch (e) {
          console.log(`Could not kill process ${pid}:`, e.message);
        }
      }
      resolve();
    });
  });
}

// Start Python backend
function startPythonBackend() {
  return new Promise((resolve, reject) => {
    try {
      killPortProcess().then(() => {
        const pythonPath = path.join(__dirname, 'venv', 'Scripts', 'python.exe');
        const backendPath = __dirname;
        const args = ['-m', 'uvicorn', 'src.api.main:app', '--port', '8000'];

        console.log(`Starting Python backend at: ${pythonPath}`);
        console.log(`Working directory: ${backendPath}`);
        console.log(`Command: ${pythonPath} ${args.join(' ')}`);

        pythonProcess = spawn(pythonPath, args, {
          cwd: backendPath,
          env: {
            ...process.env,
            PYTHONPATH: '.',
          },
          stdio: ['ignore', 'pipe', 'pipe'],
        });

        pythonProcess.stdout.on('data', (data) => {
          console.log(`Backend: ${data.toString()}`);
        });

        pythonProcess.stderr.on('data', (data) => {
          console.log(`Backend ERR: ${data.toString()}`);
        });

        pythonProcess.on('close', (code) => {
          console.log(`Python process exited with code ${code}`);
          pythonProcess = null;
        });

        pythonProcess.on('error', (error) => {
          console.error(`Failed to start Python process:`, error);
          pythonProcess = null;
          reject(error);
        });

        // Start health check with retries (don't kill backend on failure)
        waitForBackend(20, (err) => {
          if (err) {
            console.warn('Backend health check timed out, opening window anyway...');
            resolve(); // don't kill the app, backend may still be starting
          } else {
            console.log('Python backend is ready');
            resolve();
          }
        });
      });
    } catch (error) {
      console.error('Error starting Python backend:', error);
      reject(error);
    }
  });
}

// Wait for backend to respond with retries
function waitForBackend(retries, callback) {
  const url = `http://localhost:${PYTHON_PORT}/health`;

  console.log(`Checking backend health (${retries} retries remaining)...`);

  const req = http.get(url, (res) => {
    if (res.statusCode === 200) {
      console.log('Backend health check passed');
      callback(null);
    } else {
      console.log(`Backend health check failed with status ${res.statusCode}, retrying...`);
      if (retries <= 0) {
        callback(new Error('Backend did not respond with 200 status after 10 attempts'));
      } else {
        setTimeout(() => waitForBackend(retries - 1, callback), 3000);
      }
    }
  });

  req.on('error', (err) => {
    console.log(`Backend health check error: ${err.message} (${retries} retries remaining)`);
    if (retries <= 0) {
      callback(new Error('Backend not reachable after 10 attempts'));
    } else {
      setTimeout(() => waitForBackend(retries - 1, callback), 3000);
    }
  });

  req.end();
}

// Create main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
    },
  });

  mainWindow.setTitle('Context Engine');

  // Set Content Security Policy
mainWindow.webContents.session.webRequest.onHeadersReceived(
  (details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self' http://localhost:8000; " +
          "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; " +
          "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; " +
          "font-src 'self' https://fonts.gstatic.com; " +
          "connect-src 'self' http://localhost:8000 http://localhost:11434 https://api.groq.com https://openrouter.ai https://api.openai.com;"
        ]
      }
    })
  }
)

  // Show loading screen first
  const loadingHtml = path.join(__dirname, 'loading.html');
  if (fs.existsSync(loadingHtml)) {
    mainWindow.loadFile(loadingHtml);
  }

  // Try to load dashboard after delay
  setTimeout(() => {
    mainWindow.loadURL(`http://localhost:${PYTHON_PORT}/dashboard`);
  }, 2000);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  mainWindow.webContents.on('crashed', () => {
    dialog.showErrorBox('Error', 'Application crashed. Please restart.');
  });
}

// IPC: Pick folder
ipcMain.handle('pick-folder', async () => {
  if (!mainWindow) return null;

  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
    buttonLabel: 'Select Project',
    title: 'Select Project Directory',
  });

  if (!result.canceled && result.filePaths.length > 0) {
    const folderPath = result.filePaths[0];
    // Store last used path
    const configPath = path.join(app.getPath('userData'), 'lastProject.json');
    fs.writeFileSync(configPath, JSON.stringify({ path: folderPath }));
    return folderPath;
  }

  return null;
});

// IPC: Get last project path
ipcMain.handle('get-project-path', () => {
  try {
    const configPath = path.join(app.getPath('userData'), 'lastProject.json');
    if (fs.existsSync(configPath)) {
      const data = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      return data.path || null;
    }
  } catch (error) {
    console.error('Error reading project path:', error);
  }
  return null;
});

// IPC: Get platform
ipcMain.handle('get-platform', () => {
  return process.platform;
});

// App lifecycle
app.on('ready', () => {
  console.log('Electron app ready, starting Python backend...');

  startPythonBackend()
    .then(() => {
      createWindow();
    })
    .catch((error) => {
      console.error('Failed to start app:', error);
      const errorMsg = error.message || String(error);
      dialog.showErrorBox(
        'Backend Start Error',
        'Failed to start Python backend:\n\n' + errorMsg + '\n\nMake sure:\n- Python 3.13 is installed\n- venv is activated\n- All dependencies are installed'
      );
      app.quit();
    });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// Cleanup on app quit
app.on('quit', () => {
  if (pythonProcess) {
    console.log('Killing Python backend process...');
    try {
      if (process.platform === 'win32') {
        require('child_process').execSync(`taskkill /PID ${pythonProcess.pid} /T /F`, {
          stdio: 'ignore',
        });
      } else {
        pythonProcess.kill('SIGTERM');
      }
    } catch (error) {
      console.error('Error killing Python process:', error);
    }
  }
});

// Handle any uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  dialog.showErrorBox('Error', 'An unexpected error occurred.');
});

