@echo off
echo ========================================
echo Maps Python Script Helper - Dev Server
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

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: docker-compose not found, trying docker compose...
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Neither docker-compose nor docker compose found.
        echo Please install Docker Compose.
        pause
        exit /b 1
    )
    set COMPOSE_CMD=docker compose
) else (
    set COMPOSE_CMD=docker-compose
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
%COMPOSE_CMD% down 2>nul
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

echo [3/3] Starting backend container with auto-reload...
echo.
echo The server will be available at: http://localhost:8000
echo Changes to backend/ and frontend/ files will auto-reload
echo Press Ctrl+C to stop the server
echo.

REM Set HOST_PROJECT_DIR for Docker-in-Docker script execution (required for volume mounts)
set PWD=%CD%

REM Start with docker-compose (preferred method)
%COMPOSE_CMD% up --build

pause

