@echo off
REM Rebuild and restart Docker containers for Windows
echo Rebuilding PyRAGDoc SSE Server...

REM Stop existing containers
echo Stopping containers...
docker compose down

REM Remove old volumes if needed (optional - uncomment the line below if you want to remove volumes)
REM echo Removing old volumes...
REM docker compose down -v

REM Note: Windows doesn't need chmod for permissions like Linux
REM The ollama-entrypoint.sh will work inside the Docker container

REM Build with no cache to ensure fresh build
echo Building containers...
docker compose build --no-cache

REM Start services
echo Starting services...
docker compose up

REM Note: Press Ctrl+C to stop the services
