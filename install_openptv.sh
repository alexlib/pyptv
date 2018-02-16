#!/bin/sh
set -ev
git clone http://github.com/openptv/openptv
cd openptv/liboptv
mkdir _build && cd _build
cmake ../
make
make verify
sudo make install
cd ../../py_bind
python setup.py build_ext -I/usr/local/include -L/usr/local/lib
python setup.py install
export PATH=$/usr/local/lib:$PATH
export LD_LIBRARY_PATH=$/usr/local/lib:$LD_LIBRARY_PATH  
python -c "import sys; print sys.path"
cd test
nosetests -v
