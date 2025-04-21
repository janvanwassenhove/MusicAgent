const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let backendProcess;

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'), // Optional
        }
    });

    // Load the Vue frontend
    win.loadFile(path.join(__dirname, '../Frontend/dist/index.html'));

    win.on('closed', () => {
        if (backendProcess) {
            backendProcess.kill();
        }
    });
}

app.whenReady().then(() => {
    // Path to app.py (your backend)
    const backendPath = path.join(__dirname, '../App/app.py');

    // Start Python backend
    backendProcess = spawn('python', [backendPath], {
        cwd: path.join(__dirname, '..'),
        shell: true,
    });

    backendProcess.stdout.on('data', (data) => {
        console.log(`PYTHON: ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
        console.error(`PYTHON ERROR: ${data}`);
    });

    backendProcess.on('close', (code) => {
        console.log(`Python backend exited with code ${code}`);
    });

    createWindow();
});

app.on('window-all-closed', () => {
    if (backendProcess) backendProcess.kill();
    if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
