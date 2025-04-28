# PyPTV
Python GUI for the OpenPTV library `liboptv`

[![Python package](https://github.com/alexlib/pyptv/actions/workflows/python-package.yml/badge.svg)](https://github.com/alexlib/pyptv/actions/workflows/python-package.yml)
[![DOI](https://zenodo.org/badge/121291437.svg)](https://zenodo.org/badge/latestdoi/121291437)
![PyPI - Version](https://img.shields.io/pypi/v/pyptv)





**PyPTV** or otherwise called **OpenPTV-Python** is the Python GUI for [OpenPTV](http://www.openptv.net). It is based on `traits`, `traitsui`, `chaco`, `enable` and `pyface` from Enthought Inc. and provides an UI *interface* the OpenPTV library that includes all the core algorithms (correspondence, tracking, calibration, etc.) written in ANSI C and has Python bindings using Cython.  

Both PyPTV and the OpenPTV library are in the development phase and continuously refactored. Please follow the development on the community mailing list:

	openptv@googlegroups.com


## Documentation:

<http://openptv-python.readthedocs.io>

## Installation instructions

Short version:

    pip install numpy
    python -m pip install pyptv --index-url https://pypi.fury.io/pyptv --extra-index-url https://pypi.org/simple


Detailed instructions for various platforms are in our documentation: 
https://openptv-python.readthedocs.io/en/latest/installation_instruction.html





Follow the instructions in our **screencasts and tutorials**:
  
  *  Tutorial 1: <http://youtu.be/S2fY5WFsFwo>  
  
  *  Tutorial 2: <http://www.youtube.com/watch?v=_JxFxwVDSt0>   
  
  *  Tutorial 3: <http://www.youtube.com/watch?v=z1eqFL5JIJc>  
  
  
Ask for help on our mailing list:

	openptv@googlegroups.com



## Working with plugins

Plugins is a system of extensions to PyPTV without the need to change the GUI

1. copy the `sequence_plugins.txt` and `tracking_plugins.txt` to the working folder
2. copy the `plugins/` directory to the working folder
3. modify the code so it performs instead of the default sequence or default tracker
4. Open the GUI and Plugins -> Choose , then run the rest: Init -> Sequence 


Note, the specific branch `plugin_remback` requires installation of the `pip install rembg[cpu]` or `pip install rembg[gpu]`


### Developers:


1. how to bump the version: ```python bump_version.py --patch```
2. how to build and publish: 
      pip install build
      python -m build
      pip install dist/pyptv-0.3.2-py3-none-any.whl
      pip install twine
      python -m twine upload dist/*

## Compatibility Notes

### NumPy Compatibility
- Minimum supported NumPy version: 1.23.5
- Tested with NumPy arrays in both float64 and uint8 formats
- Array operations maintained for image processing and coordinate transformations

### OpenPTV (optv) Compatibility
- Compatible with optv versions 0.2.9 through 0.3.0
- Core functionality tested with latest optv release
- Calibration and tracking functions verified

## Development Setup
For development work with latest NumPy:

```bash
conda create -n pyptv python=3.11
conda activate pyptv
conda install numpy>=1.23.5 optv>=0.2.9
pip install -e .
```


