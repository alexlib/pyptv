#!/bin/bash

# Stop and remove any existing containers
echo "Cleaning up any existing containers..."
docker stop pyptv-container 2>/dev/null || true
docker rm pyptv-container 2>/dev/null || true

# Create data directory if it doesn't exist
mkdir -p data

# Create a Dockerfile
echo "Creating Dockerfile..."
cat > Dockerfile.pyptv << 'EOF'
FROM consol/ubuntu-xfce-vnc:latest

USER 0

# Install system dependencies
RUN apt-get update && apt-get install -y \
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
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir numpy matplotlib pytest tqdm cython pyyaml setuptools wheel

# Install OpenPTV
RUN cd /tmp && \
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
    cd / && \
    rm -rf /tmp/openptv

# Clone PyPTV
RUN cd /headless && \
    git clone https://github.com/alexlib/pyptv.git && \
    cd pyptv && \
    pip3 install -e .

# Create desktop shortcut
RUN echo '[Desktop Entry]\n\
Version=1.0\n\
Type=Application\n\
Name=PyPTV\n\
Comment=Particle Tracking Velocimetry\n\
Exec=python3 -m pyptv.pyptv_gui\n\
Icon=\n\
Path=/headless/work\n\
Terminal=false\n\
StartupNotify=false' > /headless/Desktop/pyptv.desktop && \
    chmod +x /headless/Desktop/pyptv.desktop

# Create startup script
RUN echo '#!/bin/bash\n\
cd /headless/work\n\
python3 -m pyptv.pyptv_gui' > /headless/start_pyptv.sh && \
    chmod +x /headless/start_pyptv.sh

# Switch back to default user
USER 1000

# Set working directory
WORKDIR /headless/work
EOF

# Run the container
echo "Starting PyPTV container..."
docker run -d \
    --name pyptv-container \
    -p 6901:6901 \
    -v $(pwd)/data:/headless/work \
    -e VNC_PW='' \
    --shm-size=2g \
    --build-arg REFRESHED_AT=$(date +%Y-%m-%d) \
    $(docker build -q -f Dockerfile.pyptv .)

# Wait for container to start
echo "Waiting for container to start..."
sleep 5

# Check if container is running
if docker ps | grep -q pyptv-container; then
    echo "
PyPTV with noVNC is now running!

Access the PyPTV GUI by opening your web browser and navigating to:
http://localhost:6901/vnc.html?password=

No password is required (just press Connect).

Your local 'data' directory is mounted to /headless/work inside the container.
Any files you save there will be accessible on your host system.

To start PyPTV:
1. Double-click the PyPTV icon on the desktop, or
2. Open a terminal in the container and run: /headless/start_pyptv.sh

To stop the container, run: docker stop pyptv-container
"

    # Open browser (if available)
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:6901/vnc.html?password=
    elif command -v open &> /dev/null; then
        open http://localhost:6901/vnc.html?password=
    elif command -v start &> /dev/null; then
        start http://localhost:6901/vnc.html?password=
    fi
else
    echo "Container failed to start. Check logs with: docker logs pyptv-container"
fi
