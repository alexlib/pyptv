# Windows Installation Guide

This guide provides step-by-step instructions for installing PyPTV on Windows 10/11.

> ⚠️ **Note**: Windows installation requires additional steps compared to Linux/macOS due to compiler requirements.

## Prerequisites

### Required Software

1. **Miniconda or Anaconda**
   - Download from [miniconda.com](https://docs.conda.io/en/latest/miniconda.html)
   - Choose the Python 3.x version for Windows

2. **Git for Windows**
   - Download from [git-scm.com](https://git-scm.com/download/win)
   - Install with default settings

3. **Microsoft Visual Studio Build Tools**
   - Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
   - Install "C++ build tools" workload
   - **Alternative**: Install Visual Studio Community (includes build tools)

### System Requirements

- Windows 10 (1909 or later) or Windows 11
- 8GB RAM minimum (16GB+ recommended)
- 5GB free disk space
- Administrator privileges for installation

## Installation Steps

### Step 1: Install Miniconda

1. Download Miniconda from the official website
2. Run the installer as Administrator
3. Choose "Add Miniconda to PATH" during installation
4. Complete the installation and restart your computer

### Step 2: Install Git and Build Tools

1. Install Git for Windows with default settings
2. Install Visual Studio Build Tools:
   - Run the installer as Administrator
   - Select "C++ build tools" workload
   - Include "MSVC v143 - VS 2022 C++ x64/x86 build tools"
   - Include "Windows 10/11 SDK"

### Step 3: Set Up PyPTV

Open **Anaconda Prompt** (or Command Prompt) as Administrator:

```cmd
# 1. Clone the repository
git clone https://github.com/openptv/pyptv.git
cd pyptv

# 2. Create conda environment
conda env create -f environment.yml

# 3. Activate the environment
conda activate pyptv

# 4. Install additional Windows dependencies
conda install -c conda-forge cmake ninja

# 5. Install PyPTV
pip install -e .
```

### Step 4: Windows-Specific Setup

For Windows, you may need to set environment variables:

```cmd
# Set up compiler environment (if needed)
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

# Install PyPTV with explicit compiler
pip install -e . --global-option build_ext --global-option --compiler=msvc
```

## Alternative Installation Methods

### Method 1: Using Windows Subsystem for Linux (WSL)

If you have WSL2 installed, you can follow the Linux installation guide:

```bash
# In WSL2 terminal
git clone https://github.com/openptv/pyptv.git
cd pyptv
./install_pyptv.sh
```

Note: GUI applications require X11 forwarding setup.

### Method 2: Using Pre-built Binaries (When Available)

Check the [releases page](https://github.com/openptv/pyptv/releases) for Windows binaries:

```cmd
# Download and extract the release
# Follow included instructions
```

## Testing Installation

Verify your installation:

```cmd
# Activate the environment
conda activate pyptv

# Test import
python -c "import pyptv; print('PyPTV installed successfully!')"

# Launch GUI (should open without errors)
python -m pyptv.pyptv_gui
```

## Common Windows Issues

### Issue: "Microsoft Visual C++ 14.0 is required"
**Solution**: Install Visual Studio Build Tools as described above.

### Issue: "cmake not found"
**Solution**: Install cmake via conda:
```cmd
conda activate pyptv
conda install -c conda-forge cmake
```

### Issue: "Failed to build optv"
**Solution**: Ensure Visual Studio Build Tools are properly installed:
```cmd
# Verify compiler
where cl
# Should show path to Microsoft C++ compiler

# Reinstall with verbose output
pip install -e . -v
```

### Issue: "Permission denied" errors
**Solution**: Run Anaconda Prompt as Administrator:
- Right-click "Anaconda Prompt"
- Select "Run as administrator"
- Retry installation

### Issue: Long path names causing errors
**Solution**: Enable long paths in Windows:
1. Open Group Policy Editor (`gpedit.msc`)
2. Navigate to: Computer Configuration → Administrative Templates → System → Filesystem
3. Enable "Enable Win32 long paths"

## GPU Acceleration (Optional)

For improved performance with large datasets:

```cmd
conda activate pyptv
# Install CUDA-enabled OpenCV (if you have NVIDIA GPU)
conda install -c conda-forge opencv cuda-toolkit
```

## Environment Management

### Daily Usage
Always activate the PyPTV environment before use:
```cmd
conda activate pyptv
python -m pyptv.pyptv_gui
```

### Creating Desktop Shortcut

Create a batch file `PyPTV.bat`:
```batch
@echo off
call conda activate pyptv
python -m pyptv.pyptv_gui
pause
```

Save it to your desktop and double-click to launch PyPTV.

### Updating PyPTV

```cmd
conda activate pyptv
cd pyptv
git pull origin main
pip install -e .
```

## Troubleshooting

### Performance Issues
- Ensure Windows Defender excludes the PyPTV directory
- Close unnecessary background applications
- Consider using SSD storage for image sequences

### Display Issues
- Update graphics drivers
- Try different display scaling settings
- Ensure sufficient graphics memory

### File Path Issues
- Avoid spaces in file paths
- Use forward slashes (/) in Python scripts
- Keep experiment directories close to drive root

## Next Steps

Once PyPTV is installed on Windows:

1. **Test Installation**: Follow the [Quick Start Guide](quick-start.md)
2. **Set Up Data**: Learn about [parameter configuration](parameter-migration.md)
3. **Start Tracking**: See [Running the GUI](running-gui.md)

## Windows-Specific Tips

- **File Organization**: Keep experiment folders in `C:\PyPTV\experiments\` for shorter paths
- **Antivirus**: Add PyPTV directories to antivirus exclusions
- **Updates**: Windows may reset some settings after major updates
- **Backup**: Regularly backup your experiment parameters

## Getting Help

For Windows-specific issues:

- Check [Windows-tagged issues](https://github.com/openptv/pyptv/issues?q=label%3Awindows) on GitHub
- Include Windows version and Python version in bug reports
- Share the full error message and installation log

---

**Next**: [Quick Start Guide](quick-start.md) or back to [Main Installation Guide](installation.md)
