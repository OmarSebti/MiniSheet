const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

let dataFile;
let mainWindow;

app.whenReady().then(() => {
  dataFile = path.join(app.getPath('userData'), 'minisheet_data.json');
  createWindow();
});

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 780,
    height: 500,
    minWidth: 580,
    minHeight: 380,
    title: 'MiniSheet',
    backgroundColor: '#f2f2f2',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile('index.html');
  mainWindow.setMenuBarVisibility(false);
}

ipcMain.handle('load-data', () => {
  try {
    if (fs.existsSync(dataFile)) {
      return JSON.parse(fs.readFileSync(dataFile, 'utf8'));
    }
  } catch (_) { /* fall through */ }
  return null;
});

ipcMain.on('save-data', (_event, payload) => {
  try {
    fs.writeFileSync(dataFile, JSON.stringify(payload, null, 2), 'utf8');
  } catch (e) {
    console.error('Save failed:', e.message);
  }
});

app.on('window-all-closed', () => app.quit());
