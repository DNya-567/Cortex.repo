const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  pickFolder: () => ipcRenderer.invoke('pick-folder'),
  getProjectPath: () => ipcRenderer.invoke('get-project-path'),
  getPlatform: () => ipcRenderer.invoke('get-platform'),
});

