const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  loadData:  ()       => ipcRenderer.invoke('load-data'),
  saveData:  (payload) => ipcRenderer.send('save-data', payload),
});
