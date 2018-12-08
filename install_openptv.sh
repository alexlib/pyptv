#!/bin/sh
set -ev
cd openptv/liboptv
mkdir _build && cd _build
cmake ../
make
make verify
cd ../../py_bind
python setup.py build_ext -I../liboptv/include -L../liboptv/build/src
python setup.py install
export PATH=$PATH:/usr/local/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/usr/local/lib
echo $LD_LIBRARY_PATH
echo $PATH
python -c "import sys; print sys.path"
cd test
nosetests -v
