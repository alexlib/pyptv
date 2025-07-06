# PyPTV Documentation

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

## Getting Help

- 📖 **Documentation**: You're reading it! Start with [Quick Start](quick-start.md)
- 🐛 **Issues**: Report bugs on [GitHub Issues](https://github.com/openptv/pyptv/issues)
- 💬 **Discussions**: Join the [GitHub Discussions](https://github.com/openptv/pyptv/discussions)
- 📧 **Contact**: Reach out to the development team

## Contributing

PyPTV is an open-source project and welcomes contributions! See our contributing guidelines for more information.

---

*Ready to get started? Begin with the [Installation Guide](installation.md) or jump to [Quick Start](quick-start.md) if you already have PyPTV installed.*
