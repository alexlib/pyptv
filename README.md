# PyPTV
Python GUI for the OpenPTV library `liboptv`


[![Build Status](https://travis-ci.org/alexlib/pyptv.svg?branch=master)](https://travis-ci.org/alexlib/pyptv) [![DOI](https://zenodo.org/badge/121291437.svg)](https://zenodo.org/badge/latestdoi/121291437)




**PyPTV** or otherwise called **OpenPTV-Python** is the Python GUI for [OpenPTV](http://www.openptv.net). It is based on `traits`, `traitsui`, `chaco`, `enable` and `pyface` from Enthought Inc. and provides an UI *interface* the OpenPTV library that includes all the core algorithms (correspondence, tracking, calibration, etc.) written in ANSI C and has Python bindings using Cython.  

Both PyPTV and the OpenPTV library are in the development phase and continuously refactored. Please follow the development on the community mailing list:

	openptv@googlegroups.com


## Documentation:

<http://openptv-python.readthedocs.io>

## Installation instructions

https://openptv-python.readthedocs.io/en/latest/installation_instruction.html

	python -m pip install --upgrade pip
	pip install numpy
	pip install pyptv --index-url https://pypi.fury.io/pyptv --extra-index-url https://pypi.org/simple
	

You might need to patch the `enable`:  

	cp .\pyptv\pathdata.py C:\users\alex\miniconda3\envs\pyptv3\lib\site-packages\enable\savage\svg\


Follow the instructions in our **screencasts and tutorials**:
  
  *  Tutorial 1: <http://youtu.be/S2fY5WFsFwo>  
  
  *  Tutorial 2: <http://www.youtube.com/watch?v=_JxFxwVDSt0>   
  
  *  Tutorial 3: <http://www.youtube.com/watch?v=z1eqFL5JIJc>  
  
  
Ask for help on our mailing list:

	openptv@googlegroups.com



