git clone http://github.com/openptv/openptv
cd $TRAVIS_BUILD_DIR/openptv/liboptv
mkdir _build && cd _build
cmake ../
make
make verify
sudo make install
cd ../../py_bind
python setup.py build_ext -I/usr/local/include -L/usr/local/lib
python setup.py install
