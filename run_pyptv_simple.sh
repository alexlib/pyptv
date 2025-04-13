#!/bin/bash

# Stop and remove any existing containers
echo "Cleaning up any existing containers..."
docker stop pyptv-container 2>/dev/null || true
docker rm pyptv-container 2>/dev/null || true

# Create data directory if it doesn't exist
mkdir -p data

# Run the container with a simple approach
echo "Starting PyPTV container..."
docker run -d \
    --name pyptv-container \
    -p 6080:80 \
    -v $(pwd)/data:/home/ubuntu/work \
    -e RESOLUTION=1280x720 \
    -e USER=ubuntu \
    -e PASSWORD= \
    --shm-size=2g \
    dorowu/ubuntu-desktop-lxde-vnc

# Wait for container to start
echo "Waiting for container to start..."
sleep 5

# Check if container is running
if docker ps | grep -q pyptv-container; then
    echo "Container started successfully. Now installing PyPTV..."
    
    # Install PyPTV in the container
    docker exec -it pyptv-container bash -c "
        # Install system dependencies
        apt-get update && \
        apt-get install -y \
            wget \
            git \
            build-essential \
            cmake \
            check \
            libsubunit-dev \
            pkg-config \
            python3 \
            python3-pip \
            python3-setuptools \
            python3-wheel \
            libgl1-mesa-glx \
            libglib2.0-0 && \
        
        # Install Python dependencies
        pip3 install --no-cache-dir numpy matplotlib pytest tqdm cython pyyaml setuptools wheel && \
        
        # Install OpenPTV
        cd /tmp && \
        git clone https://github.com/openptv/openptv && \
        cd openptv/liboptv && \
        mkdir -p build && cd build && \
        cmake ../ && \
        make && \
        make install && \
        cd ../../py_bind && \
        python3 setup.py prepare && \
        python3 setup.py build_ext --inplace && \
        python3 -m pip install . && \
        
        # Clone PyPTV
        cd /home/ubuntu && \
        git clone https://github.com/alexlib/pyptv.git && \
        cd pyptv && \
        pip3 install -e . && \
        
        # Create desktop shortcut
        echo '[Desktop Entry]
Version=1.0
Type=Application
Name=PyPTV
Comment=Particle Tracking Velocimetry
Exec=python3 -m pyptv.pyptv_gui
Icon=
Path=/home/ubuntu/work
Terminal=false
StartupNotify=false' > /home/ubuntu/Desktop/pyptv.desktop && \
        chmod +x /home/ubuntu/Desktop/pyptv.desktop && \
        
        # Create startup script
        echo '#!/bin/bash
cd /home/ubuntu/work
python3 -m pyptv.pyptv_gui' > /home/ubuntu/start_pyptv.sh && \
        chmod +x /home/ubuntu/start_pyptv.sh
    "
    
    echo "
PyPTV with noVNC is now running!

Access the PyPTV GUI by opening your web browser and navigating to:
http://localhost:6080

No password is required.

Your local 'data' directory is mounted to /home/ubuntu/work inside the container.
Any files you save there will be accessible on your host system.

To start PyPTV:
1. Double-click the PyPTV icon on the desktop, or
2. Open a terminal in the container and run: /home/ubuntu/start_pyptv.sh

To stop the container, run: docker stop pyptv-container
"

    # Open browser (if available)
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:6080
    elif command -v open &> /dev/null; then
        open http://localhost:6080
    elif command -v start &> /dev/null; then
        start http://localhost:6080
    fi
else
    echo "Container failed to start. Check logs with: docker logs pyptv-container"
fi
