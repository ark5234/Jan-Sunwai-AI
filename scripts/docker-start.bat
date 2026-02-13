@echo off
echo Starting Jan-Sunwai AI with Docker...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop first.
    pause
    exit /b 1
)

echo Building and starting containers...
docker-compose up -d --build

echo.
echo Waiting for services to be ready...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Jan-Sunwai AI is now running!
echo ========================================
echo Backend API: http://localhost:8000
echo MongoDB: mongodb://localhost:27017
echo.
echo To view logs: docker-compose logs -f
echo To stop: docker-compose down
echo.

pause
