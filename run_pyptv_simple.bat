@echo off
echo Cleaning up any existing containers...
docker stop pyptv-container 2>nul || ver>nul
docker rm pyptv-container 2>nul || ver>nul

echo Creating data directory...
if not exist data mkdir data

echo Starting PyPTV container...
docker run -d ^
    --name pyptv-container ^
    -p 6080:80 ^
    -v "%cd%\data:/home/ubuntu/work" ^
    -e RESOLUTION=1280x720 ^
    -e USER=ubuntu ^
    -e PASSWORD= ^
    --shm-size=2g ^
    dorowu/ubuntu-desktop-lxde-vnc

echo Waiting for container to start...
timeout /t 5 /nobreak > nul

echo Container started successfully. Now installing PyPTV...

docker exec -it pyptv-container bash -c "apt-get update && apt-get install -y wget git build-essential cmake check libsubunit-dev pkg-config python3 python3-pip python3-setuptools python3-wheel libgl1-mesa-glx libglib2.0-0 && pip3 install --no-cache-dir numpy matplotlib pytest tqdm cython pyyaml setuptools wheel && cd /tmp && git clone https://github.com/openptv/openptv && cd openptv/liboptv && mkdir -p build && cd build && cmake ../ && make && make install && cd ../../py_bind && python3 setup.py prepare && python3 setup.py build_ext --inplace && python3 -m pip install . && cd /home/ubuntu && git clone https://github.com/alexlib/pyptv.git && cd pyptv && pip3 install -e . && echo '[Desktop Entry]\nVersion=1.0\nType=Application\nName=PyPTV\nComment=Particle Tracking Velocimetry\nExec=python3 -m pyptv.pyptv_gui\nIcon=\nPath=/home/ubuntu/work\nTerminal=false\nStartupNotify=false' > /home/ubuntu/Desktop/pyptv.desktop && chmod +x /home/ubuntu/Desktop/pyptv.desktop && echo '#!/bin/bash\ncd /home/ubuntu/work\npython3 -m pyptv.pyptv_gui' > /home/ubuntu/start_pyptv.sh && chmod +x /home/ubuntu/start_pyptv.sh"

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
echo To start PyPTV:
echo 1. Double-click the PyPTV icon on the desktop, or
echo 2. Open a terminal in the container and run: /home/ubuntu/start_pyptv.sh
echo.
echo To stop the container, run: docker stop pyptv-container
echo.

echo Opening browser...
start http://localhost:6080

pause
