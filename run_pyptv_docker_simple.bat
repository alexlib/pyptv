@echo off
echo Creating data directory...
if not exist data mkdir data

echo Creating Dockerfile...
(
echo FROM dorowu/ubuntu-desktop-lxde-vnc:latest
echo.
echo # Set environment variables
echo ENV USER=ubuntu ^
echo     PASSWORD= ^
echo     RESOLUTION=1280x720
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
echo RUN cd /home/ubuntu ^&^& \
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
echo Path=/home/ubuntu/work\n\
echo Terminal=false\n\
echo StartupNotify=false' ^> /home/ubuntu/Desktop/pyptv.desktop ^&^& \
echo     chmod +x /home/ubuntu/Desktop/pyptv.desktop
echo.
echo # Create startup script
echo RUN echo '#!/bin/bash\n\
echo cd /home/ubuntu/work\n\
echo python3 -m pyptv.pyptv_gui' ^> /home/ubuntu/start_pyptv.sh ^&^& \
echo     chmod +x /home/ubuntu/start_pyptv.sh
echo.
echo # Set working directory
echo WORKDIR /home/ubuntu/work
) > Dockerfile.simple

echo Creating docker-compose file...
(
echo version: '3'
echo.
echo services:
echo   pyptv:
echo     build:
echo       context: .
echo       dockerfile: Dockerfile.simple
echo     container_name: pyptv-simple
echo     ports:
echo       - "6080:80"  # noVNC web interface
echo     volumes:
echo       - ./data:/home/ubuntu/work  # Mount local data directory
echo     environment:
echo       - USER=ubuntu
echo       - PASSWORD=
echo       - RESOLUTION=1280x720
echo     restart: unless-stopped
echo     shm_size: '2gb'  # Increase shared memory for X server
) > docker-compose.simple.yml

echo Building and starting the PyPTV Docker container...
docker-compose -f docker-compose.simple.yml up -d --build

echo Waiting for container to start...
timeout /t 5 /nobreak > nul

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
echo To stop the container, run: docker-compose -f docker-compose.simple.yml down
echo.

echo Opening browser...
start http://localhost:6080

pause
