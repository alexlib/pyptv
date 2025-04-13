#!/bin/bash

# Install PyPTV in the running container
docker exec -it pyptv-desktop bash -c "
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
    chmod +x /home/ubuntu/Desktop/pyptv.desktop
"

echo "
PyPTV has been installed in the container.

You can now:
1. Access the desktop at http://localhost:6080
2. Double-click the PyPTV icon on the desktop
3. Or run PyPTV from the terminal inside the container with: python3 -m pyptv.pyptv_gui
"
