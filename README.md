# PyPTV
Python GUI for the OpenPTV library `liboptv`


[![Build Status](https://travis-ci.org/alexlib/pyptv.svg?branch=master)](https://travis-ci.org/alexlib/pyptv) [![DOI](https://zenodo.org/badge/121291437.svg)](https://zenodo.org/badge/latestdoi/121291437)




**PyPTV** or otherwise called **OpenPTV-Python** is the Python GUI for [OpenPTV](http://www.openptv.net). It is based on `traits`, `traitsui`, `chaco`, `enable` and `pyface` from Enthought Inc. and provides an UI *interface* the OpenPTV library that includes all the core algorithms (correspondence, tracking, calibration, etc.) written in ANSI C and has Python bindings using Cython.  

Both PyPTV and the OpenPTV library are in the development phase and continuously refactored. Please follow the development on the community mailing list:

	openptv@googlegroups.com


## Documentation, including installation instructions of liboptv

<http://openptv-python.readthedocs.io>


## Installing this package, pyptv, using Anaconda:

        	git clone --recursive http://github.com/alexlib/pyptv.git pyptv
        	cd pyptv
        	conda create -n pyptv python=2.7 numpy=1.10 cython scikit-image chaco enable kiwisolver nose future

### Activate your package, enter the `liboptv` bindings and add the `optv` to the packages:

		conda activate pyptv
		cd ~/pyptv/openptv/py_bind
		python setup.py prepare
		python setup.py build
		python setup.py install
		cd test
		nosetests

## Getting started:

Get a test folder: 
		
		cd ~/pyptv
		git clone https://github.com/openptv/test_cavity

If the compilation passed, you can run the GUI:  
		
		cd ~/pyptv/pyptv
		python pyptv_gui.py ../test_cavity
		
or:  

		pythonw pyptv_gui/pyptv_gui.py ../test_cavity
		
It is possible to install wxPython instead of PyQt4, and switch between those:  

		ETS_TOOLKIT=qt4 python pyptv_gui/pyptv_gui.py ../test_cavity

Follow the instructions in our **screencasts and tutorials**:
  
  *  Tutorial 1: <http://youtu.be/S2fY5WFsFwo>  
  
  *  Tutorial 2: <http://www.youtube.com/watch?v=_JxFxwVDSt0>   
  
  *  Tutorial 3: <http://www.youtube.com/watch?v=z1eqFL5JIJc>  
  
  
Ask for help on our mailing list:

	openptv@googlegroups.com



