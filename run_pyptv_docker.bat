@echo off
echo Creating data directory...
if not exist data mkdir data

echo Building and starting the container...
docker-compose up -d

echo.
echo PyPTV with noVNC is now running!
echo.
echo Access the PyPTV GUI by opening your web browser and navigating to:
echo http://localhost:6080/vnc.html
echo.
echo When prompted for a password, enter: pyptv
echo.
echo Your local 'data' directory is mounted to /home/pyptv/work inside the container.
echo Any files you save there will be accessible on your host system.
echo.
echo To stop the container, run: docker-compose down
echo.

echo Opening browser...
start http://localhost:6080/vnc.html

pause
