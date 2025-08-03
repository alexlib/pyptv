# PyPTV is the GUI and batch processing software for 3D Particle Tracking Velocimetry (PTV)

### Using PyPTV

# PyPTV Documentation Index

Welcome to the PyPTV documentation! This index provides an organized overview of all available guides and resources. Use this page as your starting point for learning, troubleshooting, and reference.

## Getting Started
- [Installation Guide](installation.md)
- [Windows Installation Guide](windows-installation.md)
- [Quick Start Guide](quick-start.md)

## Core Usage
- [Running the GUI](running-gui.md)
- [YAML Parameters Reference](yaml-parameters.md)
- [Parameter Migration Guide](parameter-migration.md)
- [Calibration Guide](calibration.md)
- [Examples and Workflows](examples.md)

## Advanced Features
- [Splitter Mode Guide](splitter-mode.md)
- [Plugins System Guide](plugins.md)

## System Administration
- [Logging Guide](LOGGING_GUIDE.md)
- [Environment Guide](PYPTV_ENVIRONMENT_GUIDE.md)

## Additional Resources
- [Test Cavity Example](examples.md#test-cavity)
- [Parameter Migration FAQ](parameter-migration.md#common-migration-issues)

---

**How to use this documentation:**
- Click any link above to jump to the relevant guide.
- Use your browser's search to find keywords or topics.
- For troubleshooting, check the FAQ sections in each guide.
- For community help, visit [GitHub Issues](https://github.com/openptv/pyptv/issues) or [Discussions](https://github.com/openptv/pyptv/discussions).

---

*Documentation last updated: August 2025 for PyPTV 2025*

Welcome to PyPTV - the open-source 3D Particle Tracking Velocimetry software.

## Table of Contents

### Getting Started
- [📦 Installation Guide](installation.md) - Install PyPTV on Linux/macOS
- [🪟 Windows Installation](windows-installation.md) - Special instructions for Windows users
- [🚀 Quick Start](quick-start.md) - Get up and running with your first experiment

### Using PyPTV
- [💻 Running the GUI](running-gui.md) - Launch and use the PyPTV graphical interface
- [� YAML Parameters Reference](yaml-parameters.md) - Complete parameter documentation
- [📹 Calibration Guide](calibration.md) - Camera calibration procedures and best practices
- [� Parameter Migration](parameter-migration.md) - Convert legacy formats to modern YAML
- [� Examples and Workflows](examples.md) - Practical examples using test_cavity dataset

### Additional Resources
- [📋 Logging Guide](LOGGING_GUIDE.md) - Understanding PyPTV's logging system
- [🐍 Environment Guide](PYPTV_ENVIRONMENT_GUIDE.md) - Python environment management

## What is PyPTV?

PyPTV is a Python-based implementation of 3D Particle Tracking Velocimetry (PTV), enabling you to:

- **Track particles in 3D space** from multiple camera views
- **Measure fluid velocities** in experimental setups
- **Calibrate camera systems** for accurate 3D reconstruction
- **Process image sequences** with customizable algorithms
- **Export tracking data** for further analysis

## Key Features

✅ **Modern YAML Configuration** - Single-file parameter management  
✅ **Graphical User Interface** - Intuitive operation and visualization  
✅ **Multi-Camera Support** - 2-4 camera systems with flexible setup  
✅ **Plugin Architecture** - Extend functionality with custom algorithms  
✅ **Cross-Platform** - Runs on Linux, macOS, and Windows  
✅ **Open Source** - MIT license with active community development  

## System Requirements

- **Operating System**: Linux (Ubuntu/Debian recommended), macOS, or Windows 10/11
- **Python**: 3.11 or newer
- **Memory**: 8GB RAM minimum (16GB+ recommended for large datasets)
- **Storage**: 2GB free space (plus space for your experimental data)

## Quick Installation

For most users, follow these steps:

```bash
# Clone the repository
git clone https://github.com/openptv/pyptv
cd pyptv

# Run the installation script (Linux/macOS)
./install_pyptv.sh

# Or use conda directly
conda env create -f environment.yml
conda activate pyptv
pip install -e .
```

For detailed installation instructions, see the [Installation Guide](installation.md).

## Testing: Headless vs GUI

PyPTV separates tests into two categories:

- **Headless tests** (no GUI): Located in `tests/`. These run in CI (GitHub Actions) and Docker, and do not require a display.
- **GUI-dependent tests**: Located in `tests_gui/`. These require a display and are run locally or with Xvfb.

To run all tests locally:
```bash
bash run_tests.sh
```
To run only headless tests (recommended for CI/Docker):
```bash
bash run_headless_tests.sh
```

## Environment Setup

PyPTV uses a modern `environment.yml` and `requirements-dev.txt` for reproducible environments. Most dependencies are installed via conda, but some (e.g., `optv`, `opencv-python-headless`, `rembg`, `flowtracks`) are installed via pip in the conda environment.

See [PYPTV_ENVIRONMENT_GUIDE.md](PYPTV_ENVIRONMENT_GUIDE.md) for details.

## Docker Usage

For headless testing and reproducible builds, you can use Docker:
```bash
docker build -t pyptv-test .
docker run --rm pyptv-test
```
This runs only headless tests in a minimal environment, mimicking CI.

## Getting Help

- 📖 **Documentation**: You're reading it! Start with [Quick Start](quick-start.md)
- 🐛 **Issues**: Report bugs on [GitHub Issues](https://github.com/openptv/pyptv/issues)
- 💬 **Discussions**: Join the [GitHub Discussions](https://github.com/openptv/pyptv/discussions)
- 📧 **Contact**: Reach out to the development team

## Contributing

PyPTV is an open-source project and welcomes contributions! See our contributing guidelines for more information.

---

*Ready to get started? Begin with the [Installation Guide](installation.md) or jump to [Quick Start](quick-start.md) if you already have PyPTV installed.*

## Complete Documentation Overview

The PyPTV documentation is organized into the following sections:

### 1. Getting Started
- **[Installation Guide](installation.md)** - Complete setup for Linux/macOS
- **[Windows Installation](windows-installation.md)** - Windows-specific installation
- **[Quick Start](quick-start.md)** - 10-minute tutorial using test_cavity

### 2. Running PyPTV  
- **[Running the GUI](running-gui.md)** - Launch and use the graphical interface

### 3. Parameter Management
- **[Parameter Migration](parameter-migration.md)** - Convert from legacy .par files to YAML
- **[YAML Parameters Reference](yaml-parameters.md)** - Complete parameter documentation

### 4. Camera Calibration
- **[Calibration Guide](calibration.md)** - Step-by-step calibration procedures

### 5. Specialized Features
- **[Splitter Mode](splitter-mode.md)** - Beam splitter stereo camera systems
- **[Plugins System](plugins.md)** - Custom tracking and sequence processing

### 6. Examples and Workflows
- **[Examples and Workflows](examples.md)** - Practical examples with test_cavity

### 7. System Administration
- **[Logging Guide](LOGGING_GUIDE.md)** - Understanding PyPTV's logging
- **[Environment Guide](PYPTV_ENVIRONMENT_GUIDE.md)** - Python environment management

## Key Improvements

This documentation has been completely restructured to provide:

✅ **Modern YAML Focus** - All examples use the current YAML parameter system  
✅ **Correct num_cams Usage** - No references to obsolete `n_img` field  
✅ **test_cavity Reference** - Consistent examples using the included test dataset  
✅ **Modular Structure** - Each topic in its own focused guide  
✅ **Practical Workflows** - Step-by-step procedures for common tasks  
✅ **Cross-Referenced** - Links between related topics  
✅ **Up-to-Date** - Reflects current PyPTV 2025 functionality  

## Quick Navigation

| I want to... | Go to... |
|---------------|----------|
| Install PyPTV | [Installation Guide](installation.md) or [Windows Install](windows-installation.md) |
| Get started quickly | [Quick Start Guide](quick-start.md) |
| Run the software | [Running the GUI](running-gui.md) |
| Convert old parameters | [Parameter Migration](parameter-migration.md) |
| Understand YAML format | [YAML Parameters Reference](yaml-parameters.md) |
| Calibrate cameras | [Calibration Guide](calibration.md) |
| See examples | [Examples and Workflows](examples.md) |
| Use splitter cameras | [Splitter Mode](splitter-mode.md) |
| Create custom plugins | [Plugins System](plugins.md) |
| Troubleshoot issues | Check individual guides for troubleshooting sections |

---

*Documentation last updated: July 2025 for PyPTV 2025*
