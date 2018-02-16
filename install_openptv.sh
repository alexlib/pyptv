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
export PATH=$PATH:/usr/local/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
echo $LD_LIBRARY_PATH
echo $PATH
python -c "import sys; print sys.path"
cd test
nosetests -v
