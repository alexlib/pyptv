# Project Title

[![Python application](https://github.com/alexlib/pyptv/actions/workflows/python-app.yml/badge.svg)](https://github.com/alexlib/pyptv/actions/workflows/python-app.yml)
[![DOI](https://zenodo.org/badge/121291437.svg)](https://zenodo.org/badge/latestdoi/121291437)
[![PyPI - Version](https://img.shields.io/pypi/v/pyptv)](https://pypi.org/project/pyptv/)





**PyPTV** or otherwise called **OpenPTV-Python** is the Python GUI for [OpenPTV](http://www.openptv.net). It is based on `traits`, `traitsui`, `chaco`, `enable` and `pyface` from Enthought Inc. and provides an UI *interface* the OpenPTV library that includes all the core algorithms (correspondence, tracking, calibration, etc.) written in ANSI C and has Python bindings using Cython.  

Both PyPTV and the OpenPTV library are in the development phase and continuously refactored. Please follow the development on the community mailing list:

  openptv@googlegroups.com


## Documentation:

 👉 **[View PyPTV documentation](https://alexlib.github.io/pyptv)**
 👉 **[View OpenPTV documentation](https://openptv-python.readthedocs.io/en/latest/))**

## Installation instructions

### Using uv (recommended for development)

This project uses [uv](https://github.com/astral-sh/uv) for fast dependency management. A local wheel of `optv>=0.3.2` is included in the `wheels/` directory until it's available on PyPI.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Or to create environment from scratch
rm -rf .venv && uv sync
```

The `uv.toml` configuration automatically uses the local wheel from `wheels/`. The `uv.lock` file pins all dependencies for reproducible builds.

### Using pip

Short version:

    pip install numpy
    python -m pip install pyptv --index-url https://pypi.fury.io/pyptv --extra-index-url https://pypi.org/simple

**Note:** If `optv>=0.3.2` is not yet available on PyPI, install it from the local wheel first:

    pip install wheels/optv-0.3.2-*.whl
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

**Version Management:**
- Bump version: ```python bump_version.py --patch```

**Publishing to PyPI:**
- See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment instructions using GitHub Actions and trusted publishing

**Legacy Manual Publishing:**
```bash
pip install build
python -m build
pip install dist/pyptv-*.whl  # Install the built wheel
pip install twine
python -m twine upload dist/*
```

## Compatibility Notes

### NumPy Compatibility
- Supported NumPy versions: >=2.0.0,<2.7
- NumPy 2.x required for optv 0.3.2+
- Tested with NumPy arrays in both float64 and uint8 formats
- Array operations maintained for image processing and coordinate transformations
- NumPy 2.x support requires chaco>=6.1.0 and enable>=6.1.0

### OpenPTV (optv) Compatibility
- Compatible with optv 0.3.2+
- optv 0.3.2+ requires NumPy >=2.0.0
- Core functionality tested with latest optv release
- Calibration and tracking functions verified

## Development Setup
For development work with latest NumPy:

```bash
conda create -n pyptv python=3.11
conda activate pyptv
conda install numpy>=1.23.5 optv>=0.3.0
pip install -e .
```

## Marimo UIs (uv)

This repo includes Marimo-based interactive UIs.

Run the Detection UI:

```bash
uv pip install marimo
uv run marimo run pyptv/marimo_ui_detection.py
```

Or use the helper script:

```bash
./run_marimo_detection.sh
```

Run the Parameters UI:

```bash
uv pip install marimo
uv run marimo run pyptv/marimo_ui_parameters.py
```

Or use the helper script:

```bash
./run_marimo_parameters.sh
```


This is a detailed description of the project...
