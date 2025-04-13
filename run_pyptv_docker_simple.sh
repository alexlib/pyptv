#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p data

# Create a Dockerfile
cat > Dockerfile.simple << 'EOF'
FROM dorowu/ubuntu-desktop-lxde-vnc:latest

# Set environment variables
ENV USER=ubuntu \
    PASSWORD= \
    RESOLUTION=1280x720

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
RUN cd /home/ubuntu && \
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
Path=/home/ubuntu/work\n\
Terminal=false\n\
StartupNotify=false' > /home/ubuntu/Desktop/pyptv.desktop && \
    chmod +x /home/ubuntu/Desktop/pyptv.desktop

# Create startup script
RUN echo '#!/bin/bash\n\
cd /home/ubuntu/work\n\
python3 -m pyptv.pyptv_gui' > /home/ubuntu/start_pyptv.sh && \
    chmod +x /home/ubuntu/start_pyptv.sh

# Set working directory
WORKDIR /home/ubuntu/work
EOF

# Create a docker-compose file
cat > docker-compose.simple.yml << 'EOF'
version: '3'

services:
  pyptv:
    build:
      context: .
      dockerfile: Dockerfile.simple
    container_name: pyptv-simple
    ports:
      - "6080:80"  # noVNC web interface
    volumes:
      - ./data:/home/ubuntu/work  # Mount local data directory
    environment:
      - USER=ubuntu
      - PASSWORD=
      - RESOLUTION=1280x720
    restart: unless-stopped
    shm_size: '2gb'  # Increase shared memory for X server
EOF

# Build and start the container
echo "Building and starting the PyPTV Docker container..."
docker-compose -f docker-compose.simple.yml up -d --build

# Wait for container to start
echo "Waiting for container to start..."
sleep 5

# Print instructions
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

To stop the container, run: docker-compose -f docker-compose.simple.yml down
"

# Open browser (if available)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:6080
elif command -v open &> /dev/null; then
    open http://localhost:6080
elif command -v start &> /dev/null; then
    start http://localhost:6080
fi
