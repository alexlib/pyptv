#!/bin/bash

if [ -d "~/ptv-build" ]; then
    echo This script recreates the ptv-build directory from scratch.
    echo Please erase ~/ptv-build and start again
    exit 1
fi

mkdir ~/ptv-build
mkdir ~/ptv-build/wheels

cd ~/ptv-build
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install wheel
pip install numpy
pip install cython

# Set the path for Swig (don't forget to run get-swig before)
export PATH=~/swig/swig-3.0.12:$PATH
# enable
#yum -y install mesa-libGLU-devel
 
# Enable 4.7.2 uses old Cython, which doesn't support Python 3.7. They have a fix on master, but it wasn't released yet
# Hopefully a future version of enable will include this fix and we'll just be able to use it
# For now, we check out the entire repository, use the 4.7.2 tag but patch the file from its own commit
git clone https://github.com/enthought/enable.git --branch 4.8.1

cd enable

python setup.py bdist_wheel

cp dist/* ~/ptv-build/wheels

# chaco
# Chaco has the same problem as enable, in the file downsample/_lttb.c
# We fix it the same way, by getting just this file from the commit that fixed the issue
cd ~/ptv-build
git clone https://github.com/enthought/chaco.git --branch 4.8.0

cd chaco

python setup.py bdist_wheel
cp dist/* ~/ptv-build/wheels

# Traits
cd ~/ptv-build
git clone https://github.com/enthought/traits.git --branch 5.1.2 --single-branch --depth 1
cd traits
python setup.py bdist_wheel
cp dist/* ~/ptv-build/wheels

# Traits UI
cd ~/ptv-build
git clone https://github.com/enthought/traitsui.git --branch 6.1.1 --single-branch --depth 1
cd traitsui

# traitsui has just one wheel that is independent of the Python version, but we compile it build - just to make sure
python setup.py bdist_wheel
cp dist/* ~/ptv-build/wheels

