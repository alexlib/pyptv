@echo off
echo Cleaning up any existing containers...
docker stop pyptv-container 2>nul || ver>nul
docker rm pyptv-container 2>nul || ver>nul

echo Creating data directory...
if not exist data mkdir data

echo Creating Dockerfile...
(
echo FROM consol/ubuntu-xfce-vnc:latest
echo.
echo USER 0
echo.
echo # Install system dependencies
echo RUN apt-get update ^&^& apt-get install -y \
echo     wget \
echo     git \
echo     build-essential \
echo     cmake \
echo     check \
echo     libsubunit-dev \
echo     pkg-config \
echo     python3 \
echo     python3-pip \
echo     python3-setuptools \
echo     python3-wheel \
echo     libgl1-mesa-glx \
echo     libglib2.0-0 \
echo     ^&^& rm -rf /var/lib/apt/lists/*
echo.
echo # Install Python dependencies
echo RUN pip3 install --no-cache-dir numpy matplotlib pytest tqdm cython pyyaml setuptools wheel
echo.
echo # Install OpenPTV
echo RUN cd /tmp ^&^& \
echo     git clone https://github.com/openptv/openptv ^&^& \
echo     cd openptv/liboptv ^&^& \
echo     mkdir -p build ^&^& cd build ^&^& \
echo     cmake ../ ^&^& \
echo     make ^&^& \
echo     make install ^&^& \
echo     cd ../../py_bind ^&^& \
echo     python3 setup.py prepare ^&^& \
echo     python3 setup.py build_ext --inplace ^&^& \
echo     python3 -m pip install . ^&^& \
echo     cd / ^&^& \
echo     rm -rf /tmp/openptv
echo.
echo # Clone PyPTV
echo RUN cd /headless ^&^& \
echo     git clone https://github.com/alexlib/pyptv.git ^&^& \
echo     cd pyptv ^&^& \
echo     pip3 install -e .
echo.
echo # Create desktop shortcut
echo RUN echo '[Desktop Entry]\n\
echo Version=1.0\n\
echo Type=Application\n\
echo Name=PyPTV\n\
echo Comment=Particle Tracking Velocimetry\n\
echo Exec=python3 -m pyptv.pyptv_gui\n\
echo Icon=\n\
echo Path=/headless/work\n\
echo Terminal=false\n\
echo StartupNotify=false' ^> /headless/Desktop/pyptv.desktop ^&^& \
echo     chmod +x /headless/Desktop/pyptv.desktop
echo.
echo # Create startup script
echo RUN echo '#!/bin/bash\n\
echo cd /headless/work\n\
echo python3 -m pyptv.pyptv_gui' ^> /headless/start_pyptv.sh ^&^& \
echo     chmod +x /headless/start_pyptv.sh
echo.
echo # Switch back to default user
echo USER 1000
echo.
echo # Set working directory
echo WORKDIR /headless/work
) > Dockerfile.pyptv

echo Building and starting the PyPTV Docker container...
for /f "tokens=*" %%i in ('docker build -q -f Dockerfile.pyptv .') do set IMAGE_ID=%%i

docker run -d ^
    --name pyptv-container ^
    -p 6901:6901 ^
    -v "%cd%\data:/headless/work" ^
    -e VNC_PW="" ^
    --shm-size=2g ^
    %IMAGE_ID%

echo Waiting for container to start...
timeout /t 5 /nobreak > nul

echo.
echo PyPTV with noVNC is now running!
echo.
echo Access the PyPTV GUI by opening your web browser and navigating to:
echo http://localhost:6901/vnc.html?password=
echo.
echo No password is required (just press Connect).
echo.
echo Your local 'data' directory is mounted to /headless/work inside the container.
echo Any files you save there will be accessible on your host system.
echo.
echo To start PyPTV:
echo 1. Double-click the PyPTV icon on the desktop, or
echo 2. Open a terminal in the container and run: /headless/start_pyptv.sh
echo.
echo To stop the container, run: docker stop pyptv-container
echo.

echo Opening browser...
start http://localhost:6901/vnc.html?password=

pause
