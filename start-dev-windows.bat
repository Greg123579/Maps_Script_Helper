@echo off
echo ========================================
echo Maps Python Script Helper - Dev Server
echo Windows Docker Desktop Version
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running or not accessible.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/3] Building execution sandbox image (py-exec:latest)...
docker build -t py-exec:latest backend/runner_image
if errorlevel 1 (
    echo ERROR: Failed to build py-exec image
    pause
    exit /b 1
)
echo ✓ Execution sandbox image built successfully
echo.

echo [2/3] Stopping existing containers (if any)...
docker stop maps-python-backend 2>nul
docker rm maps-python-backend 2>nul
echo.

REM Check if user_jobs.json exists as a directory (Docker mount issue) and fix it
if exist "user_jobs.json\" (
    echo WARNING: user_jobs.json exists as a directory, removing it...
    rmdir /s /q "user_jobs.json" 2>nul
)
REM Create user_jobs.json as a file if it doesn't exist
if not exist "user_jobs.json" (
    echo {} > "user_jobs.json"
)
echo.

echo [3/3] Building and starting backend container with auto-reload...
echo.
echo The server will be available at: http://localhost:8000
echo Changes to backend/ and frontend/ files will auto-reload
echo Press Ctrl+C to stop the server
echo.

REM Build the backend image
echo Building backend image...
docker build -t maps-backend:latest .
if errorlevel 1 (
    echo ERROR: Failed to build backend image
    pause
    exit /b 1
)

REM For Windows Docker Desktop with WSL2 backend, use standard socket path
REM For older Windows Docker Desktop, might need TCP connection instead
REM This assumes WSL2 backend (default in newer Docker Desktop)

REM Set your Google API Key for AI Assistant (Gemini)
REM Get your key from: https://makersuite.google.com/app/apikey
set GOOGLE_API_KEY=AIzaSyA0VLRCaWQiFLWq7Qbg2-QiQCYiVBkVXPY

echo Starting backend container...
docker run --rm -it ^
    --name maps-python-backend ^
    -p 8000:8000 ^
    -v "%CD%":/app ^
    -v "%CD%\outputs":/app/outputs ^
    -v "%CD%\library":/app/library ^
    -v "%CD%\assets":/app/assets ^
    -v "%CD%\user_jobs.json":/app/user_jobs.json ^
    -v //var/run/docker.sock:/var/run/docker.sock ^
    -e PYTHONUNBUFFERED=1 ^
    -e DOCKER_HOST=unix:///var/run/docker.sock ^
    -e HOST_PROJECT_DIR="%CD%" ^
    -e GOOGLE_API_KEY=%GOOGLE_API_KEY% ^
    maps-backend:latest

pause

