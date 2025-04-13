@echo off
echo Creating data directory...
if not exist data mkdir data

echo Building and starting the container...
docker-compose -f docker-compose.dorowu.yml up -d

echo.
echo PyPTV with noVNC is now running!
echo.
echo Access the PyPTV GUI by opening your web browser and navigating to:
echo http://localhost:6080
echo.
echo No password is required.
echo.
echo Your local 'data' directory is mounted to /home/ubuntu/work inside the container.
echo Any files you save there will be accessible on your host system.
echo.
echo To stop the container, run: docker-compose -f docker-compose.dorowu.yml down
echo.

echo Opening browser...
start http://localhost:6080

pause
