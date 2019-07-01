## Specific for Mac OS X builders

The `get-swig.sh` and `build_wheels.sh` create binary wheels using only `pip` and `virtualenv`. We could also use `conda`::  

    conda create -n pyptv_mac_wheels python=3.7
    conda activate pyptv_mac_wheels
    conda install swig 
    conda install numpy
    conda install scipy   
    
    mkdir pyptv
    cd pyptv
    mkdir ./ptv-build
    mkdir ./ptv-build/wheels

    cd ./ptv-build
    conda install pip
    
    # enable
    #yum -y install mesa-libGLU-devel

    # Enable 4.7.2 uses old Cython, which doesn't support Python 3.7. They have a fix on master, but it wasn't released yet
    # Hopefully a future version of enable will include this fix and we'll just be able to use it
    # For now, we check out the entire repository, use the 4.7.2 tag but patch the file from its own commit
    git clone https://github.com/enthought/enable.git --branch 4.7.2

    cd enable

    # Get the correct kiva/_cython_speedups.cpp
    git checkout 969c973 -- kiva/_cython_speedups.cpp

    # On Mac OS Mojave, setup.py files for kiva pass the wrong arguments 
    # to the linker. This was fixed by another commit, out of which we take only
    # the relevant files
    git checkout 77b2397 -- kiva/agg/setup.py
    git checkout 77b2397 -- kiva/quartz/setup.py

    python setup.py bdist_wheel

    cp dist/* ../ptv-build/wheels

    # chaco
    # Chaco has the same problem as enable, in the file downsample/_lttb.c
    # We fix it the same way, by getting just this file from the commit that fixed the issue
    cd ..
    git clone https://github.com/enthought/chaco.git --branch 4.7.2

    cd chaco
    git checkout 14c5539 -- chaco/downsample/_lttb.c

    python setup.py bdist_wheel
    cp dist/* ../ptv-build/wheels

    # Traits
    cd ../ptv-build
    git clone https://github.com/enthought/traits.git --branch 5.1.1 --single-branch --depth 1
    cd traits
    python setup.py bdist_wheel
    cp dist/* ../ptv-build/wheels

    # Traits UI
    cd ..
    git clone https://github.com/enthought/traitsui.git --branch 6.1.1 --single-branch --depth 1
    cd traitsui

    # traitsui has just one wheel that is independent of the Python version, but we compile it build - just to make sure
    python setup.py bdist_wheel
    cp dist/* ../ptv-build/wheels
    
