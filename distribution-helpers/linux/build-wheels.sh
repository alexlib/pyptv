#!/bin/bash

mkdir -p /src

# enable
yum -y install mesa-libGLU-devel
 
cd /src
# Enable 4.7.2 uses old Cython, which doesn't support Python 3.7. They have a fix on master, but it wasn't released yet
# Hopefully a future version of enable will include this fix and we'll just be able to use it
# For now, we check out the entire repository, use the 4.7.2 tag but patch the file from its own commit
git clone https://github.com/enthought/enable.git --branch 4.8.1

cd enable

# Get the correct kiva/_cython_speedups.cpp
git checkout 969c973 -- kiva/_cython_speedups.cpp

/opt/python/cp37-cp37m/bin/pip install numpy
/opt/python/cp37-cp37m/bin/python setup.py bdist_wheel

/opt/python/cp36-cp36m/bin/pip install numpy
/opt/python/cp36-cp36m/bin/python setup.py bdist_wheel

/opt/python/cp38-cp38/bin/pip install numpy
/opt/python/cp38-cp38/bin/python setup.py bdist_wheel

cp dist/* /wheels

# chaco
# Chaco has the same problem as enable, in the file downsample/_lttb.c
# We fix it the same way, by getting just this file from the commit that fixed the issue
cd /src
git clone https://github.com/enthought/chaco.git --branch 4.8.0

cd chaco
#git checkout 14c5539 -- chaco/downsample/_lttb.c

/opt/python/cp36-cp36m/bin/python setup.py bdist_wheel
/opt/python/cp37-cp37m/bin/python setup.py bdist_wheel
/opt/python/cp38-cp38/bin/python setup.py bdist_wheel
cp dist/* /wheels

# Traits
cd /src
git clone https://github.com/enthought/traits.git --branch 5.1.2 --single-branch --depth 1
cd traits
/opt/python/cp36-cp36m/bin/python setup.py bdist_wheel
/opt/python/cp37-cp37m/bin/python setup.py bdist_wheel
/opt/python/cp38-cp38/bin/python setup.py bdist_wheel
cp dist/* /wheels

# Traits UI
cd /src
git clone https://github.com/enthought/traitsui.git --branch 6.1.1 --single-branch --depth 1
cd traitsui

# traitsui has just one wheel that is independent of the Python version, but we compile it build - just to make sure
/opt/python/cp36-cp36m/bin/python setup.py bdist_wheel
/opt/python/cp37-cp37m/bin/python setup.py bdist_wheel
/opt/python/cp38-cp38/bin/python setup.py bdist_wheel
cp dist/* /wheels

