@echo off
echo Starting MusicAgent Application...

:: Start the Python backend (app.py)
start cmd /k "cd app && python app.py"

:: Start the Vue.js frontend (npm run serve)
start cmd /k "cd frontend && npm run serve"

echo MusicAgent services are starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:8080
