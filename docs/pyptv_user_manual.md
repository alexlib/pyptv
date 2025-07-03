# PyPTV: Comprehensive User Manual for Python Particle Tracking Velocimetry

*Generated on: 2025-05-23*

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [YAML Parameters System](#yaml-parameters-system)
- [Core Concepts: PyPTV, OpenPTV C Libraries, and Cython Bindings](#core-concepts)
- [Getting Started: A Quick Tour with the Test Cavity Example](#getting-started)
- [PyPTV GUI and Workflow Overview](#gui-workflow)
- [Detailed PyPTV Functionality](#detailed-functionality)
- [API Reference (Conceptual)](#api-reference)
- [Advanced Topics](#advanced-topics)
- [Troubleshooting](#troubleshooting)
- [Contributing to PyPTV](#contributing)
- [License](#license)
- [Appendix](#appendix)

## Introduction {#introduction}

This manual provides a comprehensive guide to PyPTV, a Python-based tool for Particle Tracking Velocimetry (PTV). It covers installation, core concepts, usage, and advanced topics, with a particular focus on how PyPTV interacts with the underlying OpenPTV C libraries via Cython bindings.

### What is PyPTV?

PyPTV, also known as OpenPTV-Python, is a Python-based Graphical User Interface (GUI) designed for the OpenPTV (Open Source Particle Tracking Velocimetry) project. It provides a user-friendly environment for conducting 3D PTV analysis. ([alexlib/pyptv GitHub](https://github.com/alexlib/pyptv)). PyPTV is built utilizing the Enthought Tool Suite, leveraging components such as:

- `traits` and `traitsui`: For creating the graphical user interface elements and managing application data models.
- `chaco`: For interactive 2D plotting capabilities, essential for visualizing PTV data.
- `enable`: A low-level graphics library that underpins Chaco.
- `pyface`: An application framework providing components like windows, menus, and dialogs.

The primary purpose of PyPTV is to simplify the complex workflow of 3D PTV, making these advanced techniques accessible to a broader range of users.

### Key Features of PyPTV

- **Comprehensive PTV Workflow:** Supports the entire PTV pipeline, including camera calibration, image pre-processing, particle detection, stereo-matching (correspondence), particle tracking, and post-processing.
- **Interactive GUI:** Allows for intuitive parameter adjustment, step-by-step execution of the PTV process, and interactive visualization of intermediate and final results.
- **High-Performance Core:** Leverages the computational power of the underlying OpenPTV C libraries (`liboptv`) for numerically intensive tasks, ensuring efficient processing.
- **Plugin System:** PyPTV features a plugin system that allows for extending its functionality without modifying the core GUI. An example is the integration with `rembg` for background removal, which can be installed with `pip install rembg[cpu]` or `rembg[gpu]` for specific branches. ([PyPTV README](https://github.com/alexlib/pyptv/blob/master/README.md)).
- **Cross-Platform Compatibility:** Designed to run on Windows, Linux, and macOS.

### Relationship with OpenPTV C Libraries (`liboptv`) and Cython Bindings (`optv` package)

PyPTV serves as a high-level Python interface to the powerful OpenPTV ecosystem. The core of the processing, especially numerically intensive tasks like calibration algorithms, correspondence calculations, and tracking, is handled by `liboptv`. This is a set of C libraries developed as part of the OpenPTV project, with a specific version often maintained in repositories like [alexlib/openptv](https://github.com/alexlib/openptv) or the main [OpenPTV GitHub organization](https://github.com/OpenPTV/openptv).

To enable PyPTV (written in Python) to communicate with and utilize the functions in `liboptv` (written in C), Cython is employed. Cython creates Python bindings, which are packaged as the `optv` Python package. PyPTV directly depends on and imports this `optv` package to call the C library functions efficiently, bridging the gap between Python's ease of use and C's performance. ([OpenPTV Installation Instructions](https://openptv-python.readthedocs.io/en/latest/installation_instruction.html)).

### Target Audience

PyPTV is intended for:

- Researchers, engineers, and students in fields such as fluid mechanics, experimental physics, biomechanics, and any other domain requiring quantitative 3D tracking of particles or objects.
- Users who prefer a GUI-driven approach for complex data analysis tasks but require the performance of compiled languages like C/C++ for the core computations.
- Individuals involved in developing or customizing PTV methodologies.

## Installation {#installation}

This section outlines the prerequisites and steps for installing PyPTV on your system.

### Prerequisites

- **Python Version:** PyPTV generally requires Python 3. The `pyproject.toml` file in the [alexlib/pyptv repository](https://github.com/alexlib/pyptv) and its documentation often specifies compatible versions. For instance, documentation mentions Python 3.11 as being compatible with modern setups ([OpenPTV Installation Guide](https://openptv-python.readthedocs.io/en/latest/installation_instruction.html)), while `pyproject.toml` might list specific a NumPy version compatible with e.g. Python <=3.9 or a wider range. Always check the latest project files. As of early 2025, `numpy==1.26.4` is listed in the dependencies ([pyproject.toml snippet](https://github.com/alexlib/pyptv/blob/master/pyproject.toml)), which supports newer Python versions.
                
- **Operating Systems:** Windows, Linux, and macOS.
  - OS-specific considerations: For building from source, a C compiler (GCC on Linux, Clang on macOS, MSVC on Windows) and CMake are necessary. The [OpenPTV Installation Guide](https://openptv-python.readthedocs.io/en/latest/installation_instruction.html) mentions that on new Apple Macbook M1 machines, Enthought Python Distribution (EDM) might be recommended over Anaconda for specific Python versions (e.g., Python 3.8) due to precompiled binary availability for key dependencies.

- **Required Python Dependencies:** Key packages are listed in the `pyproject.toml` file. These include:
  - `numpy`: For numerical operations (fundamental array manipulations).
  - `optv`: The Cython bindings to the OpenPTV core C library (`liboptv`), providing the PTV algorithms.
  - `traits`, `traitsui`, `enable`, `chaco`, `pyface`: Enthought Tool Suite components for the GUI.
  - `PySide6` (or potentially PyQt): For the Qt backend of the GUI. `INSTALL.md` mentions compatibility fixes for `PySide6` and `TraitsUI` ([PyPTV INSTALL.md](https://github.com/alexlib/pyptv/blob/master/INSTALL.md)).
  - `scikit-image`: For image processing tasks.
  - `pandas`, `matplotlib`, `scipy`, `PyYAML`, `xarray`, `natsort`, `imageio`, `tifffile`, `tables`: For data handling, plotting, scientific computation, configuration, and file I/O. ([pyproject.toml snippet based on search results](https://github.com/alexlib/pyptv/blob/master/pyproject.toml)).

- **OpenPTV C Libraries (`liboptv`):** This core C library is typically bundled and installed as part of the `optv` Python package when you install `optv` or `pyptv` via pip using pre-built wheels. If pre-built wheels are unavailable for your platform/Python version, or if you are developing, you might need to compile `liboptv` from source, requiring a C compiler and CMake.

### Installation Steps

#### Recommended Method (using `pip` and pre-built packages)

The simplest way to install PyPTV is using `pip`, which will attempt to download and install PyPTV and its dependencies from the Python Package Index (PyPI) or other specified indices.

```bash
pip install pyptv
```

This command should automatically fetch `optv` (which includes `liboptv`) and other Python dependencies. In some cases, especially if using development versions or specific repositories, you might need to use alternative index URLs, as mentioned in the PyPTV documentation:

```bash
pip install pyptv --index-url https://pypi.fury.io/pyptv --extra-index-url https://pypi.org/simple
```

#### Installation from Source

For developers or those requiring customizations, installing from source might be preferable.

1. **Clone the PyPTV repository:**

```bash
git clone https://github.com/alexlib/pyptv.git
cd pyptv
```

2. **Install dependencies and PyPTV in development mode:**

```bash
pip install -e .
```

This approach installs PyPTV in "editable" mode, allowing you to modify the source code and see the effects without reinstalling. Additionally, if you need to customize the OpenPTV C library (`liboptv`), you may need to:

3. **Clone, build, and install the OpenPTV repository:**

```bash
git clone https://github.com/alexlib/openptv.git
cd openptv
mkdir build && cd build
cmake ..
make
```

After building `liboptv`, you would need to ensure that the Cython bindings (the `optv` Python package) are correctly linked to this custom-built version. The specifics might involve editing paths, replacing files, or rebuilding the Cython bindings with updated paths.

#### Using Virtual Environments

It is recommended to use a virtual environment to avoid potential conflicts with other Python packages:

```bash
# Using venv
python -m venv pyptv_env
source pyptv_env/bin/activate  # On Windows: pyptv_env\Scripts\activate

# Using conda
conda create -n pyptv_env python=3.11
conda activate pyptv_env
```

### Verifying Installation

After installation, you can verify that PyPTV is correctly installed by running:

```bash
python -c "import pyptv; print(pyptv.__version__)"
```

This should display the installed version of PyPTV. To check if the core OpenPTV Cython bindings are working:

```bash
python -c "import optv; print(optv.__version__)"
```

### Common Installation Issues and Solutions

1. **Compilation Errors with `optv` (Cython bindings):**
   - Ensure you have a compatible C compiler and development files installed (e.g., Python dev headers).
   - On Linux, you might need to install packages like `python-dev`, `python3-dev`, or similar.
   - On Windows, Microsoft Visual C++ Build Tools might be required.

2. **GUI-related Errors:**
   - Ensure that necessary Qt/PySide6 or PyQt components are installed.
   - For specific TraitsUI/PySide6 compatibility issues, check the PyPTV `INSTALL.md` for fixes or patches.

3. **Dependency Conflicts:**
   - If you encounter dependency conflicts, consider using a clean virtual environment or checking if there are specific version combinations that are known to work.

4. **Platform-Specific Issues:**
   - For Apple Silicon (M1/M2) machines, follow the specific guidance in the installation documentation, which might suggest using Enthought Python Distribution (EDM) for certain Python versions.
   - For Windows, pay attention to C compiler compatibility and potential issues with binary dependencies.

For more specific troubleshooting, consult the [PyPTV Issues](https://github.com/alexlib/pyptv/issues) page or the OpenPTV documentation.

## YAML Parameters System {#yaml-parameters-system}

*New in PyPTV 2025: Modern YAML-based parameter management*

PyPTV has transitioned from the legacy `.par` file system to a modern, unified **YAML-based parameter format**. This represents a major improvement in how PyPTV manages configuration and experimental parameters.

### What Changed

**Before (Legacy System):**
- Multiple `.par` files: `ptv.par`, `detect_plate.par`, `man_ori.par`, etc.
- Separate `plugins.json` file for plugin configuration
- Manual orientation data in `man_ori.dat`
- Difficult to version control and share

**Now (YAML System):**
- **Single `parameters.yaml` file** containing all configuration
- **Human-readable format** with comments and clear structure
- **Complete parameter sets** including plugins and manual orientation
- **Easy to edit, share, and version control**

### Quick Start with YAML Parameters

#### For New Users
Create a new experiment with YAML parameters:

```yaml
# parameters.yaml - Complete PyPTV configuration
n_cam: 4

detect_plate:
  gv_threshold_1: 80
  gv_threshold_2: 40
  gv_threshold_3: 20

man_ori:
  n_img: 4
  name_img:
    - "cam1.tif"
    - "cam2.tif" 
    - "cam3.tif"
    - "cam4.tif"

plugins:
  selected_tracking: "default"
  selected_sequence: "default"
```

#### For Existing Users (Migration)
Convert your existing parameter folders to the new YAML format:

```bash
# Convert legacy parameters to YAML
python -m pyptv.parameter_util legacy-to-yaml ./your_experiment/parameters/

# This creates parameters.yaml and backs up your original files
```

#### Converting Back (If Needed)
If you need legacy `.par` files (e.g., for older PyPTV versions):

```bash
# Convert YAML back to legacy format
python -m pyptv.parameter_util yaml-to-legacy parameters.yaml legacy_output/
```

### Key Benefits

✅ **Simplified Management**: One file instead of many  
✅ **Version Control Friendly**: Text-based format works perfectly with Git  
✅ **Easy Sharing**: Copy one file to share complete parameter sets  
✅ **Better Documentation**: Comments and clear structure  
✅ **Complete Configuration**: Includes everything in one place  

### Detailed Documentation

For comprehensive information about the YAML parameter system, including:
- Complete file structure reference
- Migration examples and troubleshooting
- Parameter section explanations
- Advanced usage and best practices

**See: [YAML Parameters Guide](yaml_parameters_guide.md)**

### Working with YAML Parameters in PyPTV

The PyPTV GUI automatically detects and loads `parameters.yaml` files. You can:

1. **Load YAML parameters** through the GUI File menu
2. **Edit parameters** using the GUI controls (automatically saves to YAML)
3. **Create parameter variants** by copying and modifying YAML files
4. **Share parameter sets** by simply copying the `parameters.yaml` file

### Migration Support

PyPTV maintains full backward compatibility:

- **Automatic detection**: PyPTV can still read legacy `.par` files
- **Seamless conversion**: Built-in tools convert between formats
- **No data loss**: All parameters and settings are preserved during conversion
- **Backup safety**: Legacy files are automatically backed up during migration

The parameter conversion utility handles all the complexity of migration, ensuring a smooth transition to the modern YAML system.

## Core Concepts: PyPTV, OpenPTV C Libraries, and Cython Bindings {#core-concepts}

To effectively use PyPTV, it's essential to understand the relationship between the Python GUI (PyPTV), the underlying C libraries (OpenPTV's `liboptv`), and the Cython bindings (`optv` package) that connect them. This section aims to clarify these relationships and explain how they work together.

### The Three-Layer Architecture

PyPTV employs a three-layer architecture:

1. **Python GUI Layer (PyPTV):** Written in Python using the Enthought Tool Suite (ETS), this layer provides the graphical interface, handles user input, manages the application workflow, and visualizes results.

2. **Cython Bindings Layer (`optv` Python package):** This intermediate layer, written in Cython, acts as a bridge between Python and C. It exposes the C library functions to Python while handling data conversions and memory management.

3. **C Core Layer (OpenPTV's `liboptv`):** This layer, written in C, contains the core computational algorithms for PTV, including calibration, correspondence, tracking, etc. It's optimized for performance and handles the numerically intensive parts of the workflow.

Here's a visual representation:

```
+------------------------------+
|   Python GUI Layer (PyPTV)   |  <- User interaction, visualization, workflow control
+------------------------------+
              ↑↓
+------------------------------+
| Cython Bindings (`optv` pkg) |  <- Python/C interface, data conversion
+------------------------------+
              ↑↓
+------------------------------+
|   C Core Layer (`liboptv`)   |  <- High-performance algorithms
+------------------------------+
```

### Key Components in Each Layer

#### Python GUI Layer (PyPTV)

- **Main GUI Class**: The `Pyptv` class, typically in `pyptv.py` or a similar file, is the entry point and main application class.
- **Calibration Module**: Interfaces for camera calibration, including GUI controls for calibration parameters and visualization of calibration results.
- **Image Processing Module**: Tools for pre-processing images, including filtering, background subtraction, and thresholding.
- **Tracking Module**: UI components for configuring and executing the tracking process, visualizing tracked particles, etc.
- **Visualization Tools**: Interactive 2D and sometimes 3D visualization tools built with Chaco/Enable for displaying images, particle positions, trajectories, etc.
- **Configuration Management**: Classes/methods for loading, saving, and managing configuration files (often in YAML format).

#### Cython Bindings Layer (`optv` Python package)

- **Cython Extension Modules**: These are `.pyx` files (Cython source files) and their compiled counterparts, which use the Cython language to define the interface between Python and C.
- **Type Definitions**: Mappings between Python data types (e.g., NumPy arrays) and C data types (e.g., C arrays, structs).
- **Function Wrappers**: Python-friendly wrappers around C functions, handling parameter conversion, error checking, and memory management.
- **Object-Oriented Interfaces**: Sometimes, the Cython bindings might provide more object-oriented Python interfaces to the procedural C code.

#### C Core Layer (`liboptv`)

- **Calibration Functions**: Algorithms for camera calibration, including least-squares optimization, epipolar geometry calculations, etc.
- **Detection Functions**: Image processing routines for detecting particles in images.
- **Correspondence Functions**: Algorithms for matching particles across multiple camera views (stereoscopic correspondence).
- **Tracking Functions**: Algorithms for tracking particles through time, often using predictive techniques like kinematic prediction, Kalman filtering, etc.
- **Utility Functions**: General-purpose utilities for I/O, memory management, error handling, etc.

### Data Flow Between Layers

Understanding how data flows through this architecture is key to effective use and potential extension of PyPTV:

1. **Python GUI → Cython Bindings:** The Python GUI collects user inputs (e.g., configuration parameters), prepares data (e.g., loads images as NumPy arrays), and calls functions in the Cython bindings layer.

2. **Cython Bindings → C Core:** The Cython bindings convert Python data structures to C-compatible formats (e.g., NumPy arrays to C arrays) and call the appropriate C functions.

3. **C Core Processing:** The C functions perform their computation and return results to the Cython bindings.

4. **Cython Bindings → Python GUI:** The Cython bindings convert the C results back to Python data structures and return them to the Python GUI.

5. **Python GUI Visualization/Storage:** The Python GUI then visualizes the results (e.g., using Chaco plots) and/or stores them (e.g., in CSV, HDF5, or custom formats).

### Example: Tracking Workflow

To illustrate this architecture in action, let's follow a simplified tracking workflow:

1. **User Interaction (Python GUI):**
   - User selects calibrated camera parameters and pre-processed images.
   - User sets tracking parameters (e.g., search radii, prediction method).
   - User initiates tracking by clicking a button.

2. **Python Preparation (Python GUI):**
   - Python code loads necessary data (camera parameters, particle coordinates).
   - Python code prepares data structures for tracking.

3. **Python-to-C Handoff (Cython Bindings):**
   - Python calls a Cython-wrapped tracking function.
   - Cython converts NumPy arrays to C arrays and Python objects to C structs.

4. **Core Computation (C Core):**
   - C tracking functions implement the tracking algorithm, which might include:
     - Predicting particle positions in the next frame.
     - Searching for candidates within a specified radius.
     - Evaluating and selecting matches based on various criteria.
   - C functions return results (e.g., track IDs, positions, etc.).

5. **C-to-Python Handoff (Cython Bindings):**
   - Cython receives the C results and converts them back to Python objects.
   - Cython handles memory cleanup for C data structures.

6. **Result Handling (Python GUI):**
   - Python GUI receives tracking results (e.g., as a list of track objects).
   - Python GUI updates its display to show the tracked particles.
   - Python GUI offers options to save the tracking results.

### Extending PyPTV

Understanding this architecture is particularly important when extending PyPTV or adapting it to new use cases:

- **Adding New GUI Features:** If you're only adding features that don't require new algorithms (e.g., new visualization methods, different file formats), you can work entirely in the Python layer.

- **Modifying Existing Algorithms:** If you need to modify existing algorithms, you'll often need to modify the C core code (`liboptv`) and potentially update the Cython bindings to reflect any changes in function signatures or data structures.

- **Adding New Algorithms:** To add new computational algorithms, you might need to:
  1. Implement the algorithms in C (or potentially Cython for simpler cases).
  2. Create Cython bindings if you implemented in C.
  3. Integrate with the Python GUI by adding new UI elements and connecting them to your new functions.

- **Plugin Development:** The plugin system mentioned in the PyPTV documentation suggests an extension mechanism that might allow adding functionality without directly modifying the core code. This could be a more maintainable way to extend PyPTV for specific use cases.

## Getting Started: A Quick Tour with the Test Cavity Example {#getting-started}

To help you get started with PyPTV, we'll walk through a simple example using the "test_cavity" dataset that is often included with PyPTV or available in its repositories. This tutorial will guide you through the basic workflow and introduce you to the key components of PyPTV.

### Prerequisites

Before starting, ensure you have:

1. **PyPTV Installed:** Following the installation steps from the previous section.
2. **Test Data:** You need the "test_cavity" dataset, which you can obtain by:
   - Checking if it's already included in your PyPTV installation.
   - Downloading it from the PyPTV repository or related resources.
   - Creating a "test_cavity" directory structure as needed.

### Step 1: Launch PyPTV

Start PyPTV from the command line:

```bash
python -m pyptv
```

Or, if you have PyPTV installed as a package with an entry point:

```bash
pyptv
```

This should open the PyPTV GUI, typically showing a startup screen or an empty workspace.

### Step 2: Set Up a New Project

1. **Create or Select a Working Directory:**
   - Use the File menu or similar navigation to create a new project or open an existing one.
   - If creating a new project, you'll need to specify a directory where project files will be stored.

2. **Configure Basic Settings:**
   - **YAML Parameters**: If you have a `parameters.yaml` file from a previous experiment, load it through File → Load Parameters. This will configure all settings at once.
   - **Manual Setup**: For new projects, specify the number of cameras you're using (for the test_cavity example, this is typically 4).
   - Set the image naming convention (e.g., "cam%d.%d" where the first "%d" is the camera number and the second is the frame number).
   - Specify the range of frames you want to process.
   - **Save Configuration**: Save your settings to a `parameters.yaml` file for future use and sharing.

3. **Load or Create a Multi-Camera Calibration:**
   - For the test_cavity example, you might already have calibration files available.
   - Navigate to the calibration section of the GUI.
   - Load the calibration files for each camera.
   - Verify the calibration visually, if possible.

### Step 3: Pre-Process Images

1. **Load Images:**
   - Navigate to the image processing section.
   - Load the images for each camera and for the frame range you want to process.

2. **Apply Pre-Processing:**
   - Apply background subtraction if necessary.
   - Apply any filters (e.g., Gaussian blur) to improve particle detection.
   - Set thresholds for particle detection.

3. **Review and Adjust:**
   - Visualize the pre-processed images to ensure particles are clearly visible.
   - Adjust parameters as needed until you're satisfied with the particle visualization.

### Step 4: Detect Particles

1. **Configure Detection Parameters:**
   - Set the particle detection criteria, such as:
     - Intensity threshold
     - Minimum/maximum particle size
     - Other relevant parameters

2. **Run Detection:**
   - Execute the particle detection for all cameras and frames.
   - This will produce target files (e.g., "cam%d.%d_targets") containing the detected particles.

3. **Verify Results:**
   - Visualize the detected particles to ensure they match what you expect.
   - Check for any false positives or false negatives and adjust parameters if necessary.

### Step 5: Establish Correspondences

1. **Configure Correspondence Parameters:**
   - Set parameters such as:
     - Epipolar distance threshold
     - Minimum number of cameras for a valid correspondence
     - Other stereo-matching criteria

2. **Run Correspondence:**
   - Execute the correspondence algorithm to match particles across different camera views.
   - This will produce rt_is files (for "real targets image space") containing the correspondences.

3. **Verify Correspondences:**
   - Visualize the correspondences to ensure accurate matching across cameras.
   - Identify and address any systematic issues in the correspondence process.

### Step 6: Track Particles

1. **Configure Tracking Parameters:**
   - Set parameters such as:
     - Search radius
     - Prediction method
     - Minimum/maximum track length
     - Other tracking criteria

2. **Run Tracking:**
   - Execute the tracking algorithm to link particles across frames.
   - This will produce ptv_is files (for "particle tracking velocimetry image space") containing the tracked particles.

3. **Verify Tracking:**
   - Visualize the tracks to ensure they represent coherent particle trajectories.
   - Check for issues like track fragmentation or incorrect linking.

### Step 7: Post-Process and Analyze Results

1. **Export Data:**
   - Export the tracking results to a format suitable for further analysis (e.g., CSV, HDF5).
   - You might have options to filter tracks based on length, velocity, or other criteria.

2. **Calculate Derived Quantities:**
   - Depending on your needs, calculate quantities like velocity, acceleration, etc.
   - PyPTV might have built-in tools for some of these calculations, or you might need to use external tools.

3. **Visualize and Interpret:**
   - Use PyPTV's visualization tools or export to other software for more advanced visualization and analysis.
   - Interpret the results in the context of your specific research question or application.

### Tips for the Test Cavity Example

- **Parameter Tuning:** The test_cavity example might have recommended parameters included with it. Starting with these can save time.

- **Validation:** Since the test_cavity is a standard example, you might find reference results to compare with your own.

- **Troubleshooting:** If something doesn't work as expected, check:
  - If all required files are in the expected locations.
  - If the file naming conventions match what PyPTV is expecting.
  - If the calibration files are correctly formatted and loaded.
  - If the pre-processing parameters are appropriate for the image quality and particle size/density.

This quick tour gives you a basic overview of the PyPTV workflow. Each step has many nuances and parameters that can be adjusted for your specific application. As you become more familiar with PyPTV, you'll develop an intuition for these adjustments and how they affect the results.

## PyPTV GUI and Workflow Overview {#gui-workflow}

The PyPTV graphical user interface (GUI) is designed to guide users through the complex process of Particle Tracking Velocimetry. This section provides a comprehensive overview of the GUI layout, core components, and the typical workflow from start to finish.

### GUI Layout and Components

When you launch PyPTV, you're presented with a GUI that typically includes these main areas:

1. **Main Menu:** Located at the top, providing access to file operations, project settings, and other top-level functions.

2. **Toolbar:** Contains commonly used tools and actions for quick access.

3. **Main Workspace:** The central area where images, calibration grids, particles, and tracks are visualized and manipulated.

4. **Control Panels:** Usually positioned on the sides (left, right, or both), these panels contain parameter controls, step-by-step workflow buttons, and information displays.

5. **Status Bar:** Located at the bottom, providing feedback on the current operation, errors, or general status.

The GUI is primarily built using the Enthought Tool Suite (ETS), specifically `traitsui` for the UI components and `chaco` for the visualization plots. This gives PyPTV a consistent look and feel across different platforms.

### Core GUI Modules

The PyPTV GUI is organized into several modules, each handling a specific aspect of the PTV process:

1. **Project Management Module:**
   - New project creation and configuration
   - Loading and saving project settings
   - Specifying image sequences and naming conventions

2. **Calibration Module:**
   - Loading and visualizing calibration images
   - Marking calibration points
   - Computing and refining camera parameters
   - Evaluating calibration quality

3. **Image Pre-Processing Module:**
   - Loading and visualizing raw images
   - Background removal
   - Filtering and enhancement
   - Threshold adjustment

4. **Particle Detection Module:**
   - Setting detection parameters
   - Executing detection algorithms
   - Visualizing and verifying detected particles

5. **Correspondence Module:**
   - Setting correspondence parameters
   - Executing stereo-matching algorithms
   - Visualizing and verifying 3D particle positions

6. **Tracking Module:**
   - Setting tracking parameters
   - Executing tracking algorithms
   - Visualizing and verifying particle tracks

7. **Analysis and Export Module:**
   - Calculating derived quantities (velocity, acceleration, etc.)
   - Statistical analysis of tracks
   - Exporting results to various formats

### Typical Workflow

The PyPTV workflow generally follows a sequential process, with opportunities for iteration and refinement at each step:

#### 1. Project Initialization

- **Create or Load a Project:**
  ```
  Main Menu → File → New Project / Open Project
  ```
  - Specify a working directory
  - Configure basic project parameters

- **Configure Cameras:**
  ```
  Control Panel → Camera Setup
  ```
  - Specify the number of cameras
  - Define the image naming convention
  - Set the frame range

#### 2. Calibration

- **Load Calibration Images:**
  ```
  Control Panel → Calibration → Load Images
  ```
  - Select calibration images for each camera

- **Mark Calibration Points:**
  ```
  Control Panel → Calibration → Mark Points
  ```
  - Manually mark calibration points or use automatic detection
  - Ensure points are consistently ordered across all cameras

- **Compute Calibration:**
  ```
  Control Panel → Calibration → Compute
  ```
  - Calculate camera parameters (intrinsic and extrinsic)
  - Review calibration quality (reprojection errors, etc.)

- **Save Calibration:**
  ```
  Control Panel → Calibration → Save
  ```
  - Store calibration parameters for future use

#### 3. Image Pre-Processing

- **Load Experimental Images:**
  ```
  Control Panel → Pre-Processing → Load Images
  ```
  - Select images for processing

- **Apply Pre-Processing:**
  ```
  Control Panel → Pre-Processing → Filters
  ```
  - Apply background subtraction
  - Apply spatial filters (Gaussian, median, etc.)
  - Set intensity thresholds

- **Review and Adjust:**
  ```
  Main Workspace → Image Display
  ```
  - Examine pre-processed images
  - Adjust parameters for optimal particle visibility

#### 4. Particle Detection

- **Configure Detection Parameters:**
  ```
  Control Panel → Detection → Parameters
  ```
  - Set intensity threshold
  - Define particle size range
  - Configure other detection criteria

- **Run Detection:**
  ```
  Control Panel → Detection → Execute
  ```
  - Process all images to identify particles

- **Verify Detection:**
  ```
  Main Workspace → Particle Display
  ```
  - Visualize detected particles overlaid on images
  - Check for false positives and negatives

#### 5. Correspondence (Stereo-Matching)

- **Configure Correspondence Parameters:**
  ```
  Control Panel → Correspondence → Parameters
  ```
  - Set epipolar distance threshold
  - Define minimum cameras for valid correspondence
  - Configure other matching criteria

- **Run Correspondence:**
  ```
  Control Panel → Correspondence → Execute
  ```
  - Process all frames to match particles across cameras

- **Verify Correspondence:**
  ```
  Main Workspace → 3D Display
  ```
  - Visualize 3D particle positions
  - Check for systematic errors or outliers

#### 6. Tracking

- **Configure Tracking Parameters:**
  ```
  Control Panel → Tracking → Parameters
  ```
  - Set search radius
  - Choose prediction method
  - Define track criteria (minimum length, etc.)

- **Run Tracking:**
  ```
  Control Panel → Tracking → Execute
  ```
  - Process all frames to link particles into tracks

- **Verify Tracking:**
  ```
  Main Workspace → Track Display
  ```
  - Visualize particle trajectories
  - Identify and address tracking issues

#### 7. Post-Processing and Analysis

- **Filter Tracks:**
  ```
  Control Panel → Analysis → Filter
  ```
  - Remove short or erratic tracks
  - Apply smoothing or other corrections

- **Calculate Derived Quantities:**
  ```
  Control Panel → Analysis → Compute
  ```
  - Calculate velocity, acceleration, etc.
  - Compute statistical measures

- **Export Results:**
  ```
  Control Panel → Analysis → Export
  ```
  - Save tracks and derived quantities to file
  - Export in specified format (CSV, HDF5, etc.)

### Interactive Elements and Visualization Tools

PyPTV's GUI includes various interactive elements and visualization tools to help users inspect and validate their data:

1. **Image Viewers:**
   - Zoom and pan functionality
   - Brightness/contrast adjustment
   - Overlays for detected particles, epipolar lines, etc.

2. **3D Visualizations:**
   - Interactive rotation and scaling
   - Different representation modes (points, vectors, etc.)
   - Color coding by velocity, track ID, or other properties

3. **Time Navigation:**
   - Frame-by-frame stepping
   - Animation playback
   - Jump to specific frames

4. **Data Inspection:**
   - Click-to-select particles or tracks
   - Display of detailed information for selected elements
   - Measurement tools for distances, angles, etc.

5. **Parameter Adjustment:**
   - Sliders, spinners, and text fields for parameter input
   - Real-time preview of parameter effects when possible
   - Parameter presets for common scenarios

### Configuration and Data Files

Throughout the workflow, PyPTV creates and manages several types of files:

1. **Project Configuration Files:**
   - Overall project settings (often in YAML format)
   - Camera configuration, including naming conventions and frame ranges

2. **Calibration Files:**
   - Camera parameters (intrinsic and extrinsic)
   - Calibration point coordinates

3. **Intermediate Data Files:**
   - Target files: containing detected particle information
   - Correspondence files: containing 3D particle positions
   - Track files: containing particle trajectories

4. **Result Files:**
   - Final tracks and derived quantities
   - Analysis results and statistics

Understanding the purpose and format of these files is helpful for troubleshooting and for more advanced usage scenarios where you might want to manually examine or modify the data.

### Workflow Tips and Best Practices

1. **Start Small:**
   - Begin with a small subset of frames to test your parameter settings.
   - Expand to the full dataset once you're confident in your settings.

2. **Incremental Verification:**
   - Verify the results of each step before proceeding to the next.
   - It's easier to fix issues at an early stage than to troubleshoot later.

3. **Parameter Tuning:**
   - Start with conservative parameters and gradually refine them.
   - Keep notes on parameter settings and their effects.

4. **Use Reference Data:**
   - When possible, use datasets with known ground truth for initial setup.
   - The test_cavity example is good for this purpose.

5. **Regular Saving:**
   - Save your project and intermediate results regularly.
   - Consider using version numbering for different parameter sets.

By understanding the PyPTV GUI and workflow, you'll be better equipped to navigate the complexities of the PTV process and achieve accurate, reliable results. The next sections will delve deeper into specific functionalities and provide more detailed guidance for each step.

## Detailed PyPTV Functionality {#detailed-functionality}

This section provides an in-depth examination of PyPTV's key functionalities, focusing on the most critical operations within the PTV workflow. For each functionality, we'll discuss the underlying algorithms, available parameters, and best practices for effective use.

### Camera Calibration

Camera calibration is a crucial first step in the PTV process, as it establishes the mapping between image coordinates and physical world coordinates.

#### Calibration Methods

PyPTV supports several calibration methods, primarily based on the Direct Linear Transformation (DLT) algorithm and its variants:

1. **Standard DLT:** The basic algorithm that establishes a linear relationship between 3D world points and their 2D image projections.

2. **Modified DLT with Distortion:** An extended version that accounts for lens distortion, typically using a radial-tangential distortion model.

3. **Tsai's Method:** An alternative calibration algorithm that separately handles intrinsic and extrinsic parameters, often used for comparison or specific cases.

#### Calibration Parameters

The main parameters that can be adjusted include:

- **Calibration Point Selection:**
  - Number of points: More points generally lead to better calibration, with a minimum of 6 required for standard DLT.
  - Distribution: Points should be well-distributed throughout the volume of interest.

- **Distortion Model:**
  - Radial coefficients: Typically k1, k2, and sometimes k3 for higher-order distortion.
  - Tangential coefficients: p1, p2 for non-symmetrical distortion effects.

- **Optimization Settings:**
  - Maximum iterations: Controls the convergence of the optimization process.
  - Convergence threshold: Determines when to stop the optimization.

#### Calibration Quality Assessment

PyPTV provides several metrics to evaluate calibration quality:

- **Reprojection Error:** The difference between the original calibration points in the image and their reprojection using the calibrated parameters.
  - RMS (Root Mean Square) value: A single value summarizing the overall error.
  - Individual point errors: Helps identify problematic points.

- **Epipolar Error:** For multi-camera setups, measures how well the epipolar geometry is satisfied.

- **Reconstructed 3D Points:** You can assess how accurately known 3D points are reconstructed.

#### Best Practices for Calibration

1. **Use a well-designed calibration target:**
   - Clear, high-contrast markers
   - Known, accurate physical dimensions
   - Rigid construction to prevent deformation

2. **Capture calibration images carefully:**
   - Stable positioning of cameras and target
   - Good lighting for clear marker visibility
   - Cover the entire volume of interest

3. **Verify calibration visually:**
   - Check reprojection of calibration points
   - Examine epipolar lines for correctness
   - Look for systematic errors in the residuals

4. **Iterative refinement:**
   - Remove or adjust problematic calibration points
   - Refine parameters with different starting values
   - Consider different distortion models if needed

### Image Pre-Processing

Effective image pre-processing is essential for reliable particle detection, aiming to enhance particle visibility while suppressing noise and background variations.

#### Background Removal Techniques

PyPTV offers several background removal methods:

1. **Static Background Subtraction:** Subtracts a single background image from all frames.
   - Useful for experiments with stable backgrounds
   - Requires a separate background image or the average of several frames

2. **Dynamic Background Estimation:** Computes background as a moving average or median.
   - Better for experiments with slow background changes
   - Parameters include the time window and weighting function

3. **Minimum Image Subtraction:** Uses the minimum intensity at each pixel over multiple frames.
   - Useful for removing static bright features
   - Most effective with high particle motion and low density

#### Image Filtering Operations

Common filters available in PyPTV include:

1. **Gaussian Filter:** Smooths the image using a Gaussian kernel.
   - Parameter: Kernel size/standard deviation
   - Reduces high-frequency noise but may blur small particles

2. **Median Filter:** Replaces each pixel with the median value in its neighborhood.
   - Parameter: Window size
   - Good for removing "salt and pepper" noise while preserving edges

3. **Top-Hat Filter:** Enhances small bright features on varying backgrounds.
   - Parameter: Structuring element size
   - Particularly useful for uneven illumination

#### Thresholding Methods

PyPTV supports various thresholding approaches:

1. **Global Thresholding:** Applies a single threshold value to the entire image.
   - Parameter: Threshold intensity value
   - Simple but may struggle with uneven illumination

2. **Adaptive Thresholding:** Computes local thresholds based on regional statistics.
   - Parameters: Window size, offset from local mean/median
   - Better for handling illumination variations

3. **Hysteresis Thresholding:** Uses two thresholds to connect strong features.
   - Parameters: High and low threshold values
   - Useful for preserving particle connectivity

#### Best Practices for Image Pre-Processing

1. **Establish a consistent workflow:**
   - Determine the optimal sequence of operations
   - Keep the same sequence across all cameras and frames

2. **Parameter selection:**
   - Start with conservative parameters
   - Gradually adjust while monitoring particle detection quality
   - Consider the physical size of particles when setting filter parameters

3. **Visual verification:**
   - Check processed images from different cameras and frames
   - Ensure particles are clearly visible against the background
   - Look for processing artifacts that might affect detection

4. **Balance noise reduction and detail preservation:**
   - Aggressive filtering reduces noise but may merge nearby particles
   - Minimal filtering preserves detail but may increase false positives

### Particle Detection

Once images are pre-processed, the next step is to detect individual particles in each camera view.

#### Detection Algorithms

PyPTV typically uses a connected-component labeling approach for particle detection:

1. **Binarization:** Converts the pre-processed grayscale image to binary using the thresholding methods mentioned earlier.

2. **Connected-Component Labeling:** Identifies connected regions of pixels in the binary image.

3. **Feature Extraction:** Calculates properties for each connected component, such as:
   - Centroid position (x, y)
   - Area (pixel count)
   - Intensity (sum or mean of original pixel values)
   - Shape descriptors (eccentricity, orientation, etc.)

#### Detection Parameters

Key parameters for particle detection include:

- **Intensity Threshold:** Determines which pixels are considered part of particles.
  - Higher values reduce false positives but may miss dim particles
  - Lower values detect more particles but increase false positives

- **Size Constraints:**
  - Minimum area: Filters out small noise artifacts
  - Maximum area: Filters out large blobs that might be overlapping particles

- **Shape Constraints:**
  - Eccentricity limits: Can filter elongated shapes that might not be valid particles
  - Roundness or solidity: Can help identify well-formed particles

#### Subpixel Positioning

For accurate tracking, PyPTV often employs subpixel refinement of particle positions:

1. **Intensity-Weighted Centroid:** Calculates the centroid weighted by pixel intensities.

2. **Gaussian Fitting:** Fits a 2D Gaussian to the intensity distribution of each particle.
   - Parameters include fitting window size and convergence criteria
   - Generally more accurate but computationally more intensive

3. **Interpolation Methods:** Various interpolation techniques to refine the centroid position.

#### Best Practices for Particle Detection

1. **Balance sensitivity and specificity:**
   - Adjust threshold and size constraints to minimize both false positives and false negatives
   - Consider the trade-off in the context of your specific experiment

2. **Evaluate detection across the image:**
   - Check for consistent detection quality in different regions
   - Pay attention to areas with varying illumination or background conditions

3. **Consider particle density:**
   - In high-density regions, more conservative parameters may help prevent merging
   - In low-density regions, more sensitive parameters can ensure detection of all particles

4. **Verify subpixel accuracy:**
   - Cross-check positions with known patterns when possible
   - Ensure consistent subpixel positions across frames for stationary particles

### Stereo-Matching (Correspondence)

Stereo-matching is the process of finding which particle images in different camera views correspond to the same physical particle.

#### Correspondence Algorithms

PyPTV typically uses epipolar geometry-based approaches:

1. **Epipolar Search:** For each particle in a reference camera, searches along (or near) the corresponding epipolar lines in other cameras.

2. **Multi-Camera Matching:** Extends the pairwise matching to multiple cameras, requiring consistency across all camera pairs.

3. **Triangulation:** Once correspondences are established, triangulates the 3D position of the particle using the calibrated camera parameters.

#### Correspondence Parameters

Important parameters include:

- **Epipolar Distance Tolerance:** The maximum allowed distance between a particle and the epipolar line.
  - Smaller values reduce false matches but may miss valid particles
  - Typically related to the calibration quality and particle detection accuracy

- **Minimum Camera Requirement:** The minimum number of cameras in which a particle must be visible.
  - Higher values (e.g., all cameras) reduce false matches but decrease the total number of reconstructed particles
  - Lower values (e.g., 2 out of 4) increase the number of reconstructed particles but may include more ambiguous matches

- **Triangulation Error Tolerance:** The maximum allowed reprojection error after triangulation.
  - Helps filter out incorrect correspondences
  - Should be consistent with the expected accuracy of the system

#### Ambiguity Resolution

When multiple potential matches exist, PyPTV may use various strategies:

1. **Best Match Selection:** Chooses the match with the smallest combined epipolar distance.

2. **Global Optimization:** Considers all potential matches simultaneously to find the globally optimal solution.

3. **Unique Matching Constraint:** Ensures that each particle in each view is used in at most one correspondence.

#### Best Practices for Stereo-Matching

1. **Start with conservative parameters:**
   - Use strict epipolar tolerances initially
   - Gradually relax constraints while monitoring the quality of matches

2. **Verify with known geometry:**
   - Check the 3D distribution of reconstructed particles
   - Ensure they conform to the expected experimental volume

3. **Examine ambiguous cases:**
   - Identify regions or frames with high correspondence ambiguity
   - Consider additional constraints or preprocessing for these cases

4. **Balance quantity and quality:**
   - Understand the trade-off between number of reconstructed particles and confidence in their accuracy
   - Adjust parameters based on the specific requirements of your analysis

### Particle Tracking

Particle tracking links the 3D particle positions across consecutive time frames to form trajectories.

#### Tracking Algorithms

PyPTV typically implements several tracking approaches:

1. **Nearest Neighbor:** Links particles based on proximity between frames.
   - Simple and fast
   - Less effective with high particle density or fast motion

2. **Kinematic Prediction:** Uses previous velocity/acceleration to predict future positions.
   - Better for particles with consistent motion
   - Parameters include the order of prediction (constant velocity, constant acceleration)

3. **Cost Function Optimization:** Defines a cost function for potential links and minimizes it.
   - More robust for complex scenes
   - Can incorporate various cost components (distance, intensity, etc.)

4. **Multi-Frame Approaches:** Considers multiple frames simultaneously for more robust tracking.
   - Better handles temporary occlusions or detection failures
   - More computationally intensive

#### Tracking Parameters

Key parameters include:

- **Search Radius:** The maximum distance a particle can travel between frames.
  - Related to the expected maximum velocity and the frame rate
  - Can be adaptive based on local flow characteristics

- **Prediction Method:** How future positions are predicted.
  - Options include constant position, constant velocity, constant acceleration
  - May include weighting of previous frames (e.g., exponential weighting)

- **Track Initialization and Termination Criteria:**
  - Minimum track length: Filters out short, potentially spurious tracks
  - Maximum link distance: Prevents unrealistic jumps
  - Gap closing parameters: Determines how to handle missing particles

#### Trajectory Filtering and Smoothing

After initial tracking, PyPTV often provides tools for refining trajectories:

1. **Outlier Detection:** Identifies and removes or corrects suspicious points in tracks.
   - Based on acceleration, curvature, or other measures
   - Can use various statistical approaches (median filters, percentile thresholds)

2. **Trajectory Smoothing:** Applies smoothing filters to reduce noise in the tracks.
   - Methods include moving average, polynomial fitting, splines
   - Parameters control the strength and window of smoothing

3. **Merging and Splitting:** Handles cases where tracks may be incorrectly broken or joined.
   - Based on spatial and temporal proximity
   - May use trajectory extrapolation to identify potential matches

#### Best Practices for Tracking

1. **Adjust parameters based on the experiment:**
   - Consider the expected particle motion (speed, acceleration)
   - Account for the frame rate and spatial resolution

2. **Verify tracks visually:**
   - Examine tracks in 3D to identify systematic issues
   - Look for unrealistic jumps, breaks, or merges

3. **Use physical constraints:**
   - Incorporate known physical limits on velocity or acceleration
   - Consider flow characteristics in different regions

4. **Iterative refinement:**
   - Start with conservative tracking parameters
   - Gradually adjust while monitoring track quality
   - Consider different algorithms for different experimental conditions

### Data Export and Analysis

After tracking, PyPTV provides tools for exporting and analyzing the results.

#### Export Formats

Common export formats include:

1. **Text/CSV Files:** Simple, human-readable format for track data.
  ```
  # Example position data structure (text format)
  frame_id particle_id x y z  # Header
  1 1 x11 y11 z11            # Frame 1, Particle 1
  1 2 x12 y12 z12            # Frame 1, Particle 2
  ...
  ```

2. **HDF5:** A hierarchical data format for larger datasets.
   - More efficient for large experiments
   - Supports metadata and multiple data arrays

3. **Custom Formats:** Application-specific formats for compatibility with other software.
   - May include formats for visualization tools like ParaView, Tecplot, etc.
   - Often includes header information about experiment parameters

#### Derived Quantities Calculation

PyPTV can compute various derived quantities from the tracks:

1. **Velocity and Acceleration:**
   - Computed using finite differences or more sophisticated methods
   - Parameters include the differentiation scheme and smoothing

2. **Statistical Measures:**
   - Mean, variance, and higher moments of motion properties
   - Spatial and temporal correlations
   - Probability distributions of velocity, acceleration, etc.

3. **Flow Field Reconstruction:**
   - Interpolation of particle-based measurements to regular grids
   - Methods include binning, Delaunay triangulation, and Radial Basis Function interpolation

#### Analysis Tools

PyPTV may include or integrate with tools for:

1. **Visualization:**
   - 3D trajectory rendering
   - Vector field visualization
   - Color-coding by various properties

2. **Pattern Recognition:**
   - Identification of flow structures (vortices, shear layers, etc.)
   - Classification of trajectory types

3. **Comparative Analysis:**
   - Comparison between experimental runs
   - Evaluation against theoretical models or simulations

#### Best Practices for Data Export and Analysis

1. **Document your data format:**
   - Include comprehensive metadata about the experiment
   - Clearly define units, coordinate systems, and conventions

2. **Choose appropriate differentiation methods:**
   - Consider the trade-off between noise amplification and temporal resolution
   - Use consistent methods throughout your analysis

3. **Validate derived quantities:**
   - Cross-check calculated values with known physics
   - Compare with alternative calculation methods when possible

4. **Consider uncertainty propagation:**
   - Estimate errors in position measurements
   - Propagate these errors to derived quantities like velocity

5. **Use appropriate visualization techniques:**
   - Choose visual representations that highlight relevant features
   - Consider perceptual aspects (color maps, scaling, etc.)

By mastering these detailed functionalities of PyPTV, you'll be equipped to handle a wide range of particle tracking applications, from basic flow visualization to complex quantitative analysis of 3D particle motion.

## API Reference (Conceptual) {#api-reference}

This section provides a conceptual overview of PyPTV's API structure, highlighting key classes and functions that users might interact with directly or through the GUI. While this is not a complete API reference, it aims to give you an understanding of how PyPTV's code is organized and how you might extend or customize it.

### PyPTV Python Layer (GUI and Workflow)

The PyPTV Python layer primarily consists of classes that manage the GUI, control the workflow, and coordinate interactions between the user and the underlying algorithms.

#### Main Application Classes

```python
# Conceptual representation - actual implementation may vary
class Pyptv:
    """Main application class that initializes and manages the PyPTV GUI."""
    
    def __init__(self, parameters_path=None):
        """Initialize the PyPTV application.
        
        Args:
            parameters_path (str, optional): Path to a parameter file for initialization.
        """
        # Initialize GUI components, load parameters, etc.
        
    def run(self):
        """Start the main application loop."""
        # Start the GUI event loop
```

#### Project Management Classes

```python
class Project:
    """Manages project-level data and operations."""
    
    def __init__(self, path=None):
        """Initialize a project.
        
        Args:
            path (str, optional): Path to a project directory.
        """
        # Initialize project data structure
        
    def save_parameters(self, path=None):
        """Save project parameters to a file.
        
        Args:
            path (str, optional): Path to save the parameters. Defaults to project path.
        """
        # Save parameters to a YAML file
        
    def load_parameters(self, path):
        """Load project parameters from a file.
        
        Args:
            path (str): Path to a parameter file.
        """
        # Load parameters from a YAML file
```

#### Camera and Calibration Classes

```python
class Camera:
    """Represents a single camera in the system."""
    
    def __init__(self, params=None):
        """Initialize a camera.
        
        Args:
            params (dict, optional): Camera parameters.
        """
        # Initialize camera properties
        
    def load_calibration(self, path):
        """Load calibration parameters from a file.
        
        Args:
            path (str): Path to a calibration file.
        """
        # Load calibration parameters
        
    def calibrate(self, points_2d, points_3d, method='dlt'):
        """Calibrate the camera using 2D-3D point correspondences.
        
        Args:
            points_2d (ndarray): 2D image points (Nx2).
            points_3d (ndarray): Corresponding 3D world points (Nx3).
            method (str, optional): Calibration method. Defaults to 'dlt'.
            
        Returns:
            float: RMS reprojection error.
        """
        # Call optv calibration functions through Cython bindings
```

#### Image Processing Classes

```python
class ImageProcessor:
    """Handles image loading and pre-processing operations."""
    
    def __init__(self, parameters=None):
        """Initialize the image processor.
        
        Args:
            parameters (dict, optional): Processing parameters.
        """
        # Initialize processor with default or provided parameters
        
    def load_image(self, path):
        """Load an image from file.
        
        Args:
            path (str): Path to an image file.
            
        Returns:
            ndarray: The loaded image.
        """
        # Load and return an image
        
    def subtract_background(self, image, background, method='static'):
        """Subtract background from an image.
        
        Args:
            image (ndarray): Input image.
            background (ndarray): Background image.
            method (str, optional): Background subtraction method. Defaults to 'static'.
            
        Returns:
            ndarray: Background-subtracted image.
        """
        # Perform background subtraction
        
    def filter_image(self, image, filter_type, **filter_params):
        """Apply a filter to an image.
        
        Args:
            image (ndarray): Input image.
            filter_type (str): Type of filter to apply.
            **filter_params: Parameters specific to the chosen filter.
            
        Returns:
            ndarray: Filtered image.
        """
        # Apply the specified filter
```

#### Particle Detection and Tracking Classes

```python
class ParticleDetector:
    """Detects particles in pre-processed images."""
    
    def __init__(self, parameters=None):
        """Initialize the particle detector.
        
        Args:
            parameters (dict, optional): Detection parameters.
        """
        # Initialize detector with default or provided parameters
        
    def detect_particles(self, image, threshold=None, min_size=None, max_size=None):
        """Detect particles in an image.
        
        Args:
            image (ndarray): Pre-processed image.
            threshold (float, optional): Intensity threshold.
            min_size (int, optional): Minimum particle size.
            max_size (int, optional): Maximum particle size.
            
        Returns:
            list: Detected particles with properties.
        """
        # Detect and return particles

class Tracker:
    """Tracks particles across frames."""
    
    def __init__(self, parameters=None):
        """Initialize the tracker.
        
        Args:
            parameters (dict, optional): Tracking parameters.
        """
        # Initialize tracker with default or provided parameters
        
    def track_particles(self, particles_sequence, search_radius=None, prediction_method=None):
        """Track particles across a sequence of frames.
        
        Args:
            particles_sequence (list): Sequence of particle sets for consecutive frames.
            search_radius (float, optional): Maximum search radius.
            prediction_method (str, optional): Method for predicting particle positions.
            
        Returns:
            list: Tracks connecting particles across frames.
        """
        # Track particles and return tracks
```

#### Analysis and Export Classes

```python
class Analyzer:
    """Analyzes tracking results and computes derived quantities."""
    
    def __init__(self, parameters=None):
        """Initialize the analyzer.
        
        Args:
            parameters (dict, optional): Analysis parameters.
        """
        # Initialize analyzer with default or provided parameters
        
    def compute_velocity(self, tracks, method='central_difference'):
        """Compute velocity for each point in the tracks.
        
        Args:
            tracks (list): Particle tracks.
            method (str, optional): Differentiation method. Defaults to 'central_difference'.
            
        Returns:
            list: Tracks with velocity information.
        """
        # Compute velocities and return updated tracks
        
    def export_results(self, tracks, path, format='csv'):
        """Export tracking results to a file.
        
        Args:
            tracks (list): Particle tracks.
            path (str): Path for saving the results.
            format (str, optional): Export format. Defaults to 'csv'.
        """
        # Export results in the specified format
```

### OpenPTV C Library Functions (via Cython Bindings)

The OpenPTV C library (`liboptv`) provides the core computational algorithms, which are accessed from Python through Cython bindings (`optv` package). Below are conceptual examples of some key functions.

#### Calibration Functions

```python
# These are Python representations of the Cython-wrapped C functions

def calibration_parameters_to_oriented_camera(cal_params):
    """Convert calibration parameters to an oriented camera structure.
    
    Args:
        cal_params (dict): Calibration parameters.
        
    Returns:
        OrientedCamera: A camera instance with the given parameters.
    """
    # Call corresponding C function through Cython

def point_positions(oriented_camera, targets, num_targets):
    """Calculate 3D positions from 2D targets using a calibrated camera.
    
    Args:
        oriented_camera (OrientedCamera): Calibrated camera.
        targets (list): 2D target coordinates.
        num_targets (int): Number of targets.
        
    Returns:
        ndarray: 3D positions.
    """
    # Call corresponding C function through Cython

def calibration(calibration_points, num_points, calibration_options):
    """Perform camera calibration.
    
    Args:
        calibration_points (list): 2D-3D point correspondences.
        num_points (int): Number of points.
        calibration_options (dict): Options controlling the calibration process.
        
    Returns:
        dict: Calibrated camera parameters.
    """
    # Call corresponding C function through Cython
```

#### Correspondence Functions

```python
def epipolar_curve(calibrated_cameras, target, source_camera, target_camera):
    """Calculate epipolar curve in the target camera for a point in the source camera.
    
    Args:
        calibrated_cameras (list): List of calibrated cameras.
        target (tuple): 2D coordinates in the source camera.
        source_camera (int): Index of the source camera.
        target_camera (int): Index of the target camera.
        
    Returns:
        ndarray: Epipolar curve in the target camera.
    """
    # Call corresponding C function through Cython

def find_correspondences(targets_lists, num_cameras, calibrated_cameras, tolerance):
    """Find correspondences across multiple cameras.
    
    Args:
        targets_lists (list): Lists of targets for each camera.
        num_cameras (int): Number of cameras.
        calibrated_cameras (list): List of calibrated cameras.
        tolerance (float): Epipolar distance tolerance.
        
    Returns:
        list: Correspondences across cameras.
    """
    # Call corresponding C function through Cython

def triangulate_targets(calibrated_cameras, target_matches, return_residuals=False):
    """Triangulate 3D positions from 2D target matches.
    
    Args:
        calibrated_cameras (list): List of calibrated cameras.
        target_matches (list): Matching targets across cameras.
        return_residuals (bool, optional): Whether to return residuals. Defaults to False.
        
    Returns:
        tuple: 3D positions and optionally residuals.
    """
    # Call corresponding C function through Cython
```

#### Tracking Functions

```python
def track_forward(positions_1, positions_2, max_distance, prediction=None):
    """Track particles from frame 1 to frame 2.
    
    Args:
        positions_1 (ndarray): 3D positions in frame 1.
        positions_2 (ndarray): 3D positions in frame 2.
        max_distance (float): Maximum linking distance.
        prediction (ndarray, optional): Predicted positions in frame 2. Defaults to None.
        
    Returns:
        list: Links between frames 1 and 2.
    """
    # Call corresponding C function through Cython

def predict_positions(track_history, method='constant_velocity'):
    """Predict future positions based on track history.
    
    Args:
        track_history (list): Historical positions in a track.
        method (str, optional): Prediction method. Defaults to 'constant_velocity'.
        
    Returns:
        ndarray: Predicted next position.
    """
    # Call corresponding C function through Cython
```

### Extending PyPTV

If you want to extend PyPTV with new functionality, here are some common approaches:

#### Adding a New Image Processing Filter

```python
# Add a new method to the ImageProcessor class
def enhance_particles(self, image, parameter1=default1, parameter2=default2):
    """Apply a custom particle enhancement filter.
    
    Args:
        image (ndarray): Input image.
        parameter1: First parameter for the enhancement algorithm.
        parameter2: Second parameter for the enhancement algorithm.
        
    Returns:
        ndarray: Enhanced image.
    """
    # Implement your custom enhancement algorithm
    # ...
    return enhanced_image
```

#### Creating a Custom Tracking Algorithm

```python
# Create a new class that can be used in place of or alongside the standard Tracker
class AdaptiveTracker:
    """A tracker that adapts its parameters based on local particle density."""
    
    def __init__(self, base_parameters=None):
        """Initialize the adaptive tracker.
        
        Args:
            base_parameters (dict, optional): Base tracking parameters.
        """
        self.base_parameters = base_parameters or {}
        
    def estimate_local_density(self, particles):
        """Estimate local particle density.
        
        Args:
            particles (list): Particle positions.
            
        Returns:
            ndarray: Density at each particle location.
        """
        # Implement density estimation
        # ...
        return densities
        
    def adapt_parameters(self, particles, densities):
        """Adapt tracking parameters based on local densities.
        
        Args:
            particles (list): Particle positions.
            densities (ndarray): Density at each particle location.
            
        Returns:
            dict: Adapted tracking parameters.
        """
        # Adjust parameters based on densities
        # ...
        return adapted_parameters
        
    def track_particles(self, particles_sequence):
        """Track particles with adaptive parameters.
        
        Args:
            particles_sequence (list): Sequence of particle sets for consecutive frames.
            
        Returns:
            list: Tracks connecting particles across frames.
        """
        # Implement adaptive tracking
        # ...
        return tracks
```

#### Adding a Plugin

```python
# Create a plugin class that can be loaded by PyPTV
class BackgroundModelingPlugin:
    """Plugin for advanced background modeling."""
    
    def __init__(self, parameters=None):
        """Initialize the plugin.
        
        Args:
            parameters (dict, optional): Plugin parameters.
        """
        self.parameters = parameters or {}
        
    def register(self, pyptv_instance):
        """Register the plugin with PyPTV.
        
        Args:
            pyptv_instance: Instance of the PyPTV application.
        """
        # Add menu items, toolbar buttons, etc.
        # ...
        
    def model_background(self, image_sequence):
        """Create a sophisticated background model from an image sequence.
        
        Args:
            image_sequence (list): Sequence of images.
            
        Returns:
            ndarray: Modeled background.
        """
        # Implement background modeling
        # ...
        return background_model
```

These conceptual API examples should help you understand the structure of PyPTV's code and how you might interact with or extend it. For detailed information about specific classes, methods, and parameters, refer to the source code or additional documentation in the PyPTV and OpenPTV repositories.

## Advanced Topics {#advanced-topics}

This section explores advanced topics and techniques for users who want to go beyond the basic functionality of PyPTV. These topics are particularly relevant for researchers developing new methods or adapting PyPTV to specialized applications.

### Custom Calibration Approaches

While PyPTV includes standard calibration methods, there are several advanced techniques you might consider:

#### Multi-phase Calibration

For experiments with multiple phases (e.g., air-water interfaces), standard calibration can be insufficient due to refraction:

1. **Phase-specific Calibration:**
   - Calibrate each phase separately using different calibration targets.
   - Implement interface corrections based on Snell's law.
   - Example approach: `cal_phase1` and `cal_phase2` objects with an interface model connecting them.

2. **Ray-tracing Through Interfaces:**
   - Implement a ray-tracing algorithm that accounts for refraction at interfaces.
   - Requires accurate modeling of interface geometry.
   - Can be implemented as an extension to the standard calibration pipeline.

#### Temporal Calibration Updates

For long experiments or those with potential camera movement:

1. **Incremental Calibration Updates:**
   - Periodically inject calibration targets during the experiment.
   - Implement a smoothing function for calibration parameter evolution.
   - Consider Kalman filtering for parameter updates.

2. **Self-calibration:**
   - Use particle positions themselves to refine calibration over time.
   - Implement bundle adjustment techniques for simultaneous optimization of camera parameters and particle positions.
   - Could be added as a post-processing step in the tracking pipeline.

### Advanced Particle Detection

Standard connected-component algorithms may be insufficient for certain applications. Consider these advanced approaches:

#### Overlapping Particle Separation

For high-density experiments where particles frequently overlap:

1. **Shape Analysis:**
   - Detect deviations from expected particle shapes.
   - Use watershed algorithms to separate overlapping particles.
   - Implementation example: Extended `ParticleDetector` with a `separate_overlapping` method.

2. **Model Fitting:**
   - Fit multiple Gaussian or similar models to intensity distributions.
   - Use statistical tests to determine the optimal number of particles.
   - Consider implementations using scientific Python libraries like `scipy.optimize`.

#### Dynamic Thresholding

For experiments with varying illumination or particle properties:

1. **Adaptive Local Thresholds:**
   - Compute thresholds based on local image statistics.
   - Implement as a preprocessing step before standard detection.
   - Example: `adaptiveThreshold(image, window_size, offset)` function.

2. **Machine Learning Classification:**
   - Train a classifier to distinguish particles from background/noise.
   - Features could include intensity, gradients, texture measures, etc.
   - Implementation might involve scikit-learn integration or custom classifiers.

### Correspondence in Challenging Scenarios

Standard epipolar-based matching can struggle in certain situations:

#### High Particle Density

For experiments with many particles and frequent ambiguities:

1. **Global Optimization:**
   - Formulate correspondence as a global optimization problem.
   - Implement algorithms like Hungarian method or network flow.
   - Could be an alternative mode in the correspondence module.

2. **Temporal Consistency:**
   - Use information from previous frames to constrain current correspondence.
   - Implement probabilistic assignment based on track predictions.
   - Would require tight integration between the correspondence and tracking modules.

#### Weak Calibration or Non-ideal Setups

For scenarios where calibration is imperfect or camera arrangements are suboptimal:

1. **Relaxed Epipolar Constraints:**
   - Implement adaptive epipolar tolerances based on calibration uncertainty.
   - Use probabilistic matching rather than strict thresholds.
   - Example: `find_correspondences(..., adaptive_tolerance=True)`.

2. **Additional Constraints:**
   - Incorporate intensity, size, or other particle properties in matching.
   - Implement as a scoring function within the correspondence algorithm.
   - Could be parameterized by weighting factors for different properties.

### Advanced Tracking Algorithms

Beyond the standard tracking approaches, consider these advanced techniques:

#### Multi-frame Optimization

For robust tracking in complex flows:

1. **Spatio-temporal Energy Minimization:**
   - Formulate tracking as minimizing a global energy function across multiple frames.
   - Implement graph-based algorithms or variational approaches.
   - Could be a new `MultiFrameTracker` class or an optional mode.

2. **Trajectory Pattern Matching:**
   - Detect common motion patterns and use them to guide tracking.
   - Implement clustering or template matching for trajectory segments.
   - Consider as a recovery strategy for ambiguous cases.

#### Physics-informed Tracking

For experiments where the underlying physics is known:

1. **Flow Model Integration:**
   - Incorporate flow models (e.g., Navier-Stokes solutions) in the tracking process.
   - Implement as constraints or priors in the linking algorithm.
   - Example: `track_with_flow_model(particles, flow_field, ...)`.

2. **Physical Constraints:**
   - Enforce conservation laws (mass, momentum) during tracking.
   - Implement as regularization terms in the tracking optimization.
   - Could be added as optional constraints to the standard tracker.

### Performance Optimization

For handling large datasets or real-time applications:

#### Algorithmic Optimizations

1. **Spatial Indexing:**
   - Implement efficient spatial data structures (kd-trees, octrees) for proximity queries.
   - Replace brute-force searches in correspondence and tracking.
   - Could provide significant speedup for large particle counts.

2. **Multi-scale Processing:**
   - Implement hierarchical approaches for detection and tracking.
   - Start with coarse resolution and refine progressively.
   - Particularly useful for non-uniform particle distributions.

#### Computational Optimizations

1. **Parallel Processing:**
   - Implement multi-threaded or distributed versions of key algorithms.
   - Particularly useful for independent operations (e.g., processing different frames).
   - Consider Python's multiprocessing or more advanced tools like Dask.

2. **GPU Acceleration:**
   - Port compute-intensive parts to GPU using libraries like CUDA or OpenCL.
   - Focus on naturally parallel operations (e.g., image processing, particle detection).
   - Would require significant changes to the C core or alternative implementations.

### Custom Analysis Techniques

Beyond standard tracking outputs, consider these advanced analyses:

#### Flow Field Reconstruction

For deriving continuous fields from discrete particle measurements:

1. **Adaptive Interpolation:**
   - Implement methods that account for varying particle density.
   - Consider approaches like adaptive kernel size or varying weight functions.
   - Example: `interpolate_to_grid(tracks, grid, adaptive=True)`.

2. **Physics-constrained Reconstruction:**
   - Enforce physical constraints (divergence-free for incompressible flows, etc.).
   - Implement regularization based on known physics.
   - Could be integrated with existing interpolation methods.

#### Lagrangian Coherent Structures (LCS)

For identifying transport barriers and mixing behaviors:

1. **Finite-Time Lyapunov Exponent (FTLE):**
   - Implement FTLE calculation from particle trajectories.
   - Requires dense trajectory fields and appropriate interpolation.
   - Example: `compute_ftle(tracks, grid, integration_time)`.

2. **Lagrangian Averages:**
   - Compute material derivatives and Lagrangian averages of flow properties.
   - Implement pathline integration and property accumulation.
   - Useful for understanding mixing and transport phenomena.

### Implementing Advanced Features

If you're interested in implementing any of these advanced features, here are some general guidelines:

1. **Start with a Clear API Design:**
   - Define the interface for your new feature.
   - Consider how it will integrate with existing PyPTV components.
   - Document expected inputs, outputs, and behaviors.

2. **Prototype in Python First:**
   - Implement a working version in pure Python.
   - Test with small datasets to validate the approach.
   - Only move to C/Cython once the algorithm is stable.

3. **Integration Strategy:**
   - For minor extensions, modify existing classes.
   - For substantial new functionality, create new classes or modules.
   - For alternative algorithms, consider a strategy pattern or plugin approach.

4. **Testing and Validation:**
   - Create test cases with known results.
   - Cross-check with existing methods when possible.
   - Consider synthetic data for controlled testing.

5. **Performance Considerations:**
   - Profile your implementation to identify bottlenecks.
   - Optimize critical sections, possibly moving them to Cython or C.
   - Consider memory usage for large datasets.

By exploring these advanced topics, you can extend PyPTV's capabilities to handle more challenging experimental conditions and extract more detailed information from your particle tracking data. While implementing these features may require significant effort, the resulting improvements in accuracy, robustness, or analytical capabilities can be well worth it for specialized applications.

## Troubleshooting {#troubleshooting}

This section provides guidance for identifying and resolving common issues that may arise when using PyPTV. It covers installation problems, runtime errors, and quality issues in the PTV results.

### Installation Issues

#### Missing Dependencies

**Symptoms:**
- Error messages mentioning missing modules or libraries
- Installation fails with import errors

**Solutions:**
1. **Check Python Version Compatibility:**
   ```bash
   python --version
   ```
   Ensure your Python version is compatible with PyPTV (typically Python 3.7-3.11).

2. **Install Missing Python Packages:**
   ```bash
   pip install -r requirements.txt
   ```
   Or install specific missing packages:
   ```bash
   pip install numpy scipy traits traitsui chaco pyface
   ```

3. **Install Development Libraries:**
   For Linux:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-dev cmake build-essential
   
   # Fedora/RHEL
   sudo dnf install python3-devel cmake gcc-c++ make
   ```
   For macOS:
   ```bash
   brew install cmake
   ```
   For Windows:
   - Install Microsoft Visual C++ Build Tools
   - Ensure CMake is installed

#### Compilation Errors with C Extensions

**Symptoms:**
- Errors during compilation of the optv package
- Messages about missing headers or compiler errors

**Solutions:**
1. **Check Compiler Installation:**
   ```bash
   # For GCC
   gcc --version
   
   # For MSVC on Windows
   cl
   ```

2. **Set Compiler Flags Explicitly:**
   ```bash
   export CFLAGS="-I/path/to/include"
   export LDFLAGS="-L/path/to/lib"
   pip install -e .
   ```

3. **Use Pre-built Wheels:**
   If available, try installing pre-built packages:
   ```bash
   pip install pyptv --index-url https://pypi.fury.io/pyptv --extra-index-url https://pypi.org/simple
   ```

4. **Manual Build of liboptv:**
   If automated building fails, try manual steps:
   ```bash
   git clone https://github.com/alexlib/openptv.git
   cd openptv
   mkdir build && cd build
   cmake ..
   make
   # Then copy liboptv to an appropriate location
   ```

#### Platform-Specific Issues

**Symptoms:**
- Installation works on one platform but fails on another
- Certain features work differently across platforms

**Solutions:**
1. **For Apple Silicon (M1/M2):**
   - Use Enthought Distribution for specific Python versions
   - Ensure native or properly configured Rosetta environment

2. **For Windows:**
   - Check for Windows-specific installation instructions in the PyPTV documentation
   - Ensure paths don't contain spaces or special characters
   - For GUI issues, check Qt/PySide6 installation

3. **For Linux:**
   - Check for system-specific library dependencies
   - Ensure X11 or Wayland development libraries are installed for GUI

### Runtime Errors

#### GUI Fails to Start

**Symptoms:**
- PyPTV crashes immediately after starting
- GUI elements don't appear or are rendered incorrectly

**Solutions:**
1. **Check GUI Backend:**
   ```python
   # In Python, before running PyPTV
   import traitsui
   print(traitsui.toolkit.toolkit)
   ```
   Ensure a compatible backend (e.g., 'qt4', 'qt5', 'pyside6') is available.

2. **Fix Qt/TraitsUI Compatibility:**
   If using PySide6 with older TraitsUI, check PyPTV's `INSTALL.md` for specific patches or fixes.

3. **Launch in Debug Mode:**
   ```bash
   python -m pyptv --debug
   ```
   Look for error messages that might identify the issue.

#### Crashes During Operation

**Symptoms:**
- PyPTV crashes during specific operations
- Error messages about segmentation faults or memory issues

**Solutions:**
1. **Check Input Data:**
   Verify that image files and calibration data are valid and complete.

2. **Monitor Memory Usage:**
   For large datasets, watch memory consumption and consider processing fewer frames at a time.

3. **Check for Version Conflicts:**
   ```bash
   pip list
   ```
   Look for multiple versions of the same package or known incompatibilities.

4. **Reinstall Problematic Components:**
   ```bash
   pip uninstall optv
   pip install optv
   ```
   Try reinstalling components that might be causing issues.

#### File I/O Errors

**Symptoms:**
- Cannot load or save files
- Error messages about permissions or invalid paths

**Solutions:**
1. **Check File Permissions:**
   Ensure PyPTV has read/write access to the project directory.

2. **Verify Path Conventions:**
   On Windows, check for correct path separators and potential issues with long paths.

3. **Create Directories Manually:**
   If PyPTV fails to create necessary directories, create them manually before proceeding.

### Calibration Issues

#### High Reprojection Errors

**Symptoms:**
- Large reprojection errors in calibration
- Inconsistent camera parameters

**Solutions:**
1. **Check Calibration Target:**
   - Ensure the target is rigid and not deformed
   - Verify that the physical measurements are accurate

2. **Improve Point Marking:**
   - Mark calibration points more precisely
   - Consider using automatic detection with manual verification

3. **Adjust Calibration Model:**
   - Try different distortion models
   - If using DLT, ensure enough points (at least 6, preferably more)

4. **Check for Outliers:**
   - Identify points with high reprojection errors
   - Remove or reposition problematic points

#### Inconsistent Calibration Across Cameras

**Symptoms:**
- Large epipolar errors
- Poor 3D reconstruction despite good individual camera calibrations

**Solutions:**
1. **Ensure Consistent Point Ordering:**
   Verify that calibration points are marked in the same order across all cameras.

2. **Use a Common Coordinate System:**
   Make sure all cameras reference the same world coordinate system.

3. **Consider a Global Optimization:**
   Implement a bundle adjustment approach that simultaneously optimizes all cameras.

### Particle Detection Issues

#### Missing Particles

**Symptoms:**
- Visible particles in the image are not detected
- Inconsistent detection across frames

**Solutions:**
1. **Adjust Threshold:**
   Lower the intensity threshold to detect dimmer particles.

2. **Refine Pre-processing:**
   ```
   Control Panel → Pre-Processing → Filters
   ```
   Try different filters or parameters to enhance particle visibility.

3. **Check Size Constraints:**
   Ensure minimum/maximum size settings don't exclude valid particles.

#### False Positives

**Symptoms:**
- Background noise or artifacts detected as particles
- Too many particles detected compared to expected

**Solutions:**
1. **Improve Background Subtraction:**
   Try different background models or parameters.

2. **Increase Threshold:**
   Raise the intensity threshold to exclude noise.

3. **Refine Size and Shape Criteria:**
   Set more restrictive size limits or use additional shape criteria.

### Correspondence Issues

#### Few Matched Particles

**Symptoms:**
- Many particles detected in individual views but few 3D reconstructions
- Poor reconstruction density

**Solutions:**
1. **Check Calibration Quality:**
   Verify that epipolar geometry is accurate using test points.

2. **Adjust Epipolar Tolerance:**
   Increase the tolerance to allow for calibration uncertainties.

3. **Reduce Minimum Camera Requirement:**
   If using more than 2 cameras, try allowing reconstruction with fewer cameras.

#### Ambiguous Matching

**Symptoms:**
- Incorrect correspondences between views
- Particles appearing at implausible positions

**Solutions:**
1. **Reduce Epipolar Tolerance:**
   Decrease the maximum allowed distance to enforce stricter matching.

2. **Increase Minimum Camera Requirement:**
   Require matches in more cameras for better reliability.

3. **Implement Additional Constraints:**
   Consider using intensity, size, or other properties as additional matching criteria.

### Tracking Issues

#### Fragmented Tracks

**Symptoms:**
- Tracks break frequently despite continuous particle motion
- Many short tracks instead of fewer long ones

**Solutions:**
1. **Increase Search Radius:**
   ```
   Control Panel → Tracking → Parameters → Search Radius
   ```
   Allow searching for matches at greater distances.

2. **Improve Prediction Method:**
   Switch to a more sophisticated prediction method (e.g., constant velocity or acceleration).

3. **Enable Gap Closing:**
   Configure tracking to bridge small gaps in detection.

#### Incorrect Linking

**Symptoms:**
- Tracks jump between different physical particles
- Unrealistic velocity or acceleration spikes

**Solutions:**
1. **Reduce Search Radius:**
   Decrease the maximum linking distance to prevent erroneous long-distance links.

2. **Add Motion Constraints:**
   Implement velocity or acceleration limits to prevent physically implausible tracks.

3. **Adjust Prediction Weights:**
   If using multiple frame information, adjust how historical information is weighted.

### Performance Issues

#### Slow Processing

**Symptoms:**
- Operations take excessively long to complete
- GUI becomes unresponsive during processing

**Solutions:**
1. **Process Smaller Batches:**
   Reduce the number of frames processed at once.

2. **Optimize Image Resolution:**
   Consider whether full resolution is necessary for your application.

3. **Check System Resources:**
   Monitor CPU, memory, and disk usage to identify bottlenecks.

4. **Use Caching:**
   Save intermediate results to avoid recomputation.

#### Memory Consumption

**Symptoms:**
- Out of memory errors
- System becomes sluggish during processing

**Solutions:**
1. **Process in Batches:**
   Divide the dataset into smaller chunks.

2. **Clear Unused Data:**
   Explicitly clear large arrays when no longer needed.

3. **Use Memory-Mapped Files:**
   For large datasets, consider implementation changes to use memory-mapped files.

### Advanced Troubleshooting

#### Debugging C Extensions

If you suspect issues in the C/Cython layer:

1. **Enable Debug Symbols:**
   ```bash
   CFLAGS="-g -O0" pip install -e .
   ```

2. **Use GDB for Debugging:**
   ```bash
   gdb --args python -m pyptv
   ```

3. **Add Logging to Cython Code:**
   Insert print statements or logging in Cython files (.pyx) and recompile.

#### Creating Reproducible Examples

When seeking help:

1. **Create a Minimal Example:**
   Prepare the smallest possible example that demonstrates the issue.

2. **Share Complete Environment Information:**
   ```bash
   pip freeze > requirements.txt
   python --version
   # Also include OS version and compiler information
   ```

3. **Document Steps to Reproduce:**
   Provide clear steps that others can follow to reproduce the issue.

### Community Resources

For issues not resolved by the above suggestions:

1. **GitHub Issues:**
   Check existing issues on the [PyPTV GitHub repository](https://github.com/alexlib/pyptv/issues) or create a new one.

2. **OpenPTV Community:**
   Look for help from the broader OpenPTV community, which may include forums, mailing lists, or discussion groups.

3. **Academic Literature:**
   For methodological issues, consult academic papers on PTV techniques, which may provide insights into algorithm limitations and alternatives.

By systematically addressing issues using this troubleshooting guide, you should be able to resolve most common problems encountered with PyPTV. Remember that the complex nature of PTV means that some issues may require application-specific solutions, especially for challenging experimental conditions.

## Contributing to PyPTV {#contributing}

PyPTV, like many open-source projects, benefits from community contributions. This section outlines how you can contribute to the PyPTV project, whether through code, documentation, or other forms of participation.

### Getting Started

Before making contributions, it's important to understand the project's structure and development process:

1. **Familiarize Yourself with the Code:**
   - Clone both repositories:
     ```bash
     git clone https://github.com/alexlib/pyptv.git
     git clone https://github.com/alexlib/openptv.git
     ```
   - Explore the code structure and functionality
   - Run the examples to understand how things work

2. **Set Up a Development Environment:**
   - Create a virtual environment:
     ```bash
     python -m venv pyptv_dev
     source pyptv_dev/bin/activate  # On Windows: pyptv_dev\Scripts\activate
     ```
   - Install in development mode:
     ```bash
     cd pyptv
     pip install -e .
     ```
   - Set up for testing:
     ```bash
     pip install pytest pytest-cov
     ```

3. **Understand the Development Workflow:**
   - Check the project's README and documentation for development guidelines
   - Look for a CONTRIBUTING.md file for specific instructions
   - Review open issues and pull requests to see what others are working on

### Types of Contributions

There are many ways to contribute to PyPTV, depending on your skills and interests:

#### Code Contributions

1. **Bug Fixes:**
   - Identify bugs through testing or user reports
   - Develop fixes that address the root cause
   - Submit a pull request with a clear description of the bug and solution

2. **Feature Enhancements:**
   - Improve existing features based on user feedback
   - Optimize performance of computational bottlenecks
   - Enhance the user interface for better usability

3. **New Features:**
   - Implement new algorithms for particle detection, correspondence, or tracking
   - Add support for additional file formats or visualization methods
   - Create new analysis tools for PTV data

4. **Platform Compatibility:**
   - Fix platform-specific issues
   - Improve installation or build processes
   - Enhance cross-platform support

#### Documentation Contributions

1. **Code Documentation:**
   - Add or improve docstrings in the code
   - Create or update API documentation
   - Comment complex algorithms for better maintainability

2. **User Documentation:**
   - Write or improve installation instructions
   - Create tutorials for common use cases
   - Develop detailed manuals for specific functionalities

3. **Example Creation:**
   - Develop example scripts demonstrating PyPTV features
   - Create sample datasets with expected outputs
   - Document workflows for specific applications

#### Testing Contributions

1. **Unit Tests:**
   - Write tests for individual functions or classes
   - Improve coverage of existing tests
   - Fix failing tests

2. **Integration Tests:**
   - Create tests that verify interactions between components
   - Test end-to-end workflows
   - Validate correct operation across different platforms

3. **Performance Testing:**
   - Benchmark key functionality
   - Identify performance bottlenecks
   - Verify improvements from optimization efforts

#### Community Contributions

1. **Issue Triage:**
   - Help categorize and prioritize issues
   - Reproduce reported bugs
   - Provide additional information on existing issues

2. **User Support:**
   - Answer questions from other users
   - Create FAQs or knowledge base articles
   - Develop troubleshooting guides

3. **Community Building:**
   - Organize meetups or workshops
   - Present PyPTV at relevant conferences
   - Promote awareness of the project

### Development Process

When contributing code to PyPTV, follow these steps for a smooth process:

#### 1. Choose an Issue

1. **Find an Open Issue:**
   - Check the [PyPTV GitHub issues](https://github.com/alexlib/pyptv/issues) for tasks labeled "good first issue" if you're new
   - Look for issues that match your interests and skills
   - Consider proposing a new feature if you've identified a need

2. **Claim the Issue:**
   - Comment on the issue expressing your interest
   - Ask questions if the requirements are unclear
   - Wait for a maintainer to assign the issue to you

#### 2. Create a Development Branch

1. **Fork the Repository:**
   - Create your own fork of the PyPTV repository
   - Keep your fork synchronized with the main repository

2. **Create a Feature Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or for bugfixes:
   git checkout -b fix/issue-description
   ```

#### 3. Develop Your Changes

1. **Write Clean Code:**
   - Follow the project's coding style
   - Include docstrings for all functions, classes, and methods
   - Comment complex sections of code

2. **Commit Regularly:**
   ```bash
   git add changed_files
   git commit -m "Descriptive commit message"
   ```
   - Use clear, concise commit messages
   - Reference the issue number (e.g., "Fixes #123")

3. **Test Your Changes:**
   - Add tests for new functionality
   - Ensure existing tests pass
   - Check for any regressions
   ```bash
   pytest
   ```

#### 4. Submit a Pull Request

1. **Push to Your Fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request:**
   - Go to the PyPTV repository on GitHub
   - Click "New Pull Request"
   - Select your branch and provide a detailed description

3. **Respond to Feedback:**
   - Address review comments constructively
   - Make requested changes and push updates
   - Engage in discussion about implementation details

### Coding Standards

To maintain consistency and quality, follow these guidelines when contributing code:

#### Python Code Style

1. **PEP 8 Compliance:**
   - Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
   - Use tools like flake8 or pylint to check compliance
   ```bash
   pip install flake8
   flake8 your_changed_files.py
   ```

2. **Documentation:**
   - Use [NumPy docstring format](https://numpydoc.readthedocs.io/en/latest/format.html) for Python code
   - Include examples in docstrings where appropriate
   - Document parameters, return values, and exceptions

#### C Code Style

For contributions to the C library (liboptv):

1. **Consistent Formatting:**
   - Use a consistent indentation style (typically 4 spaces)
   - Follow the existing code style for consistency

2. **Documentation:**
   - Document functions with clear comments
   - Explain complex algorithms or implementations
   - Use Doxygen-compatible comment style if the project uses it

#### Testing Requirements

1. **Test Coverage:**
   - Aim for comprehensive test coverage of new code
   - Test both normal operation and edge cases
   - Include tests for error conditions

2. **Test Organization:**
   - Place tests in the appropriate test directory
   - Name tests clearly to indicate what they're testing
   - Structure tests to be independent and repeatable

### Building and Testing

To ensure your changes work correctly, follow these steps for building and testing:

#### Building PyPTV

For Python-only changes:
```bash
cd pyptv
pip install -e .
```

For changes involving the C library or Cython bindings:
```bash
# First build liboptv if necessary
cd openptv
mkdir build && cd build
cmake ..
make

# Then install PyPTV with your changes
cd ../../pyptv
pip install -e .
```

#### Running Tests

Run the test suite to verify your changes:
```bash
cd pyptv
pytest
```

For more detailed output:
```bash
pytest -v
```

For coverage information:
```bash
pytest --cov=pyptv
```

### Documentation Generation

If you've updated documentation, verify that it builds correctly:

1. **For API Documentation:**
   - PyPTV may use tools like Sphinx for API documentation
   - Check the project's documentation for specific build instructions
   - Typically something like:
     ```bash
     cd docs
     make html
     # Then open _build/html/index.html in a browser
     ```

2. **For User Guides:**
   - Follow the format of existing user documentation
   - Preview Markdown files directly on GitHub or using tools like grip
     ```bash
     pip install grip
     grip your_documentation.md
     ```

### Getting Help

If you encounter difficulties while contributing:

1. **Ask for Guidance:**
   - Comment on the issue you're working on
   - Reach out to maintainers through appropriate channels
   - Be specific about what you're struggling with

2. **Look for Resources:**
   - Check existing documentation and examples
   - Search for similar issues or pull requests
   - Review the codebase for similar patterns

### Acknowledgment

Contributing to open-source projects like PyPTV is valuable work that benefits the scientific community. Your contributions, whether large or small, help improve the tool for everyone.

When contributing, remember that:

- All contributions are valued, from fixing typos to adding major features
- The project benefits from diverse perspectives and areas of expertise
- Good communication and collaboration make the project stronger

By following these guidelines, you can make effective contributions to PyPTV and help advance the field of particle tracking velocimetry.

## License {#license}

Understanding the licensing of PyPTV and its components is important for users who want to use, modify, or distribute the software. This section clarifies the licensing details of PyPTV, the OpenPTV C library, and related components.

### PyPTV License

PyPTV is typically released under the **GNU General Public License version 3 (GPL-3.0)** or a compatible license. The GPL is a copyleft license that ensures the software and its derivatives remain free and open-source.

Key aspects of the GPL-3.0 license for PyPTV users:

1. **Freedom to Use:** You can use PyPTV for any purpose, including commercial applications.

2. **Freedom to Study and Modify:** You can examine the source code and make modifications.

3. **Freedom to Share:** You can distribute copies of PyPTV to others.

4. **Freedom to Distribute Modified Versions:** You can distribute your modified versions, but they must also be licensed under GPL-3.0.

5. **Source Code Requirement:** If you distribute PyPTV or a derivative work, you must make the source code available.

6. **No Additional Restrictions:** You cannot impose additional restrictions on recipients beyond those in the GPL-3.0.

The full text of the GPL-3.0 license can typically be found in the LICENSE file in the PyPTV repository or on the [GNU website](https://www.gnu.org/licenses/gpl-3.0.html).

### OpenPTV C Library License

The OpenPTV C library (liboptv) is also typically released under the **GPL-3.0** license. This consistency in licensing between PyPTV and the C library simplifies compliance, as both components can be distributed together under the same terms.

### Third-Party Dependencies

PyPTV relies on various third-party libraries, each with its own license. Some common dependencies and their typical licenses include:

1. **NumPy:** BSD license (permissive)
2. **SciPy:** BSD license (permissive)
3. **Enthought Tool Suite (ETS):** Various licenses, primarily BSD or similar permissive licenses
4. **Qt/PySide/PyQt:** Depending on the version, PySide is typically LGPL, while PyQt might be GPL or commercial

When distributing PyPTV, it's important to acknowledge these third-party licenses and ensure compliance with their terms.

### License Compliance

To comply with the licensing requirements:

1. **When Using PyPTV:**
   - No special actions are required if you're simply using PyPTV for your research or applications.

2. **When Modifying PyPTV:**
   - Keep copyright notices and license statements intact.
   - Document your changes to help others understand what you modified.
   - You're not required to distribute your modified version, but if you do, it must be under GPL-3.0.

3. **When Distributing PyPTV:**
   - Include the original license and copyright notices.
   - Make the source code available, including any modifications.
   - Ensure recipients can access the complete source code.

4. **When Incorporating PyPTV in Larger Works:**
   - Be aware that the GPL's "viral" nature means the larger work may need to be GPL-compatible.
   - Consider consulting legal advice for complex integration scenarios.

### License for Outputs and Results

The GPL license applies to the software itself, not to the outputs or results produced by the software. Therefore:

1. **PTV Results:** The data and analysis results generated by PyPTV are not automatically covered by the GPL.

2. **Publications:** You can publish research papers based on PyPTV results without GPL restrictions.

3. **Custom Scripts:** If you write custom scripts that merely use PyPTV as a separate program (without incorporating its code), those scripts may not need to be GPL.

### Citing PyPTV

While not a legal requirement, it is good scientific practice to cite PyPTV when you use it in research. Typically, you should:

1. **Cite the Software:** Reference PyPTV and specify the version used.

2. **Cite Relevant Papers:** If the PyPTV documentation mentions specific papers describing the algorithms or methods, cite those as well.

3. **Acknowledge Contributors:** When appropriate, acknowledge the developers and contributors to PyPTV.

A typical citation might look like:

```
We performed 3D particle tracking using PyPTV version X.Y.Z (Smith et al., 2023), an open-source implementation of the OpenPTV algorithm.
```

### Commercial Use Considerations

The GPL-3.0 license allows commercial use of the software, but with certain obligations:

1. **Commercial Applications:** You can use PyPTV in commercial applications or services.

2. **Distribution Obligations:** If you distribute PyPTV as part of a commercial product, you must make the complete source code (including your modifications) available under GPL-3.0.

3. **Network Services:** Using PyPTV to provide a network service (without distributing the software itself) typically doesn't trigger GPL distribution requirements (the "ASP loophole").

For commercial applications with complex requirements, consider consulting legal advice about license compliance.

### License Verification

To verify the current license of PyPTV and its components:

1. **Check the LICENSE File:** Look for a LICENSE or COPYING file in the repository.

2. **Review Source File Headers:** Source files often include license information in their headers.

3. **Consult Documentation:** The official documentation may provide licensing details.

4. **Contact Maintainers:** If license information is unclear, contact the project maintainers for clarification.

Understanding and respecting the licensing terms of PyPTV and its components ensures that you can use the software legally while contributing to the sustainability of the open-source project.

## Appendix {#appendix}

This appendix provides additional reference material, glossaries, and resources to complement the main user manual.

### Glossary of Terms

#### General PTV Terminology

- **Particle Tracking Velocimetry (PTV):** A technique for measuring fluid velocities by tracking individual particles within the flow.

- **Tracer Particles:** Small particles added to a fluid to visualize and quantify the flow, ideally following the fluid motion without disturbing it.

- **Camera Calibration:** The process of determining the parameters that define how a 3D point in world coordinates projects onto a 2D image plane.

- **Intrinsic Parameters:** Camera properties such as focal length, principal point, and distortion coefficients.

- **Extrinsic Parameters:** Camera position (translation) and orientation (rotation) relative to a world coordinate system.

- **Epipolar Geometry:** The geometric relationship between two camera views of the same scene, used in correspondence matching.

- **Epipolar Line:** The line in one camera's image where a point from another camera's image might appear, based on epipolar geometry.

- **Triangulation:** The process of determining a point's 3D coordinates from its projections in multiple camera views.

- **Reprojection Error:** The distance between an observed image point and the reprojection of its estimated 3D point.

- **Trajectory:** The path followed by a particle over time, consisting of a sequence of 3D positions.

- **Lagrangian Perspective:** Analyzing fluid motion by following individual fluid particles (or tracers) over time.

- **Eulerian Perspective:** Analyzing fluid motion at fixed points in space over time.

#### PyPTV-Specific Terms

- **Target:** A detected particle in a 2D image.

- **Target File:** A file containing detected particle positions and properties for a specific camera and frame.

- **Correspondence:** A matching of targets across multiple camera views that refer to the same physical particle.

- **RT_IS File:** "Real Targets Image Space" file, containing correspondence information.

- **PTV_IS File:** "Particle Tracking Velocimetry Image Space" file, containing tracking information.

- **Calibration Parameter Set:** The collection of parameters that define a camera's calibration.

- **DLT Coefficients:** Parameters used in the Direct Linear Transformation method for camera calibration.

- **Image Coordinate System:** The 2D coordinate system of the camera image, typically with the origin at the top-left corner.

- **Physical Coordinate System:** The 3D coordinate system of the real world, defined by the calibration target.

- **Control Points:** Known 3D points used for calibration, typically marked on a calibration target.

### File Formats

PyPTV uses various file formats for storing data at different stages of the PTV process. Here's a brief description of the most common formats:

#### Configuration Files

- **Parameters Files (.par):** Text files containing various parameters for the PTV process.
  ```
  # Example parameters file structure
  8          # Number of cameras
  cam1.%d    # Image name template for camera 1
  ...
  cam8.%d    # Image name template for camera 8
  1000 1000
  0 999
  0 999
  ```

- **Calibration Files (.cal):** Text files containing camera calibration parameters.
  ```
  # Example calibration file structure
  1          # Calibration flag
  fx fy cx cy k1 k2 k3 p1 p2  # Intrinsic parameters
  R11 R12 R13                 # Rotation matrix (row 1)
  R21 R22 R23                 # Rotation matrix (row 2)
  R31 R32 R33                 # Rotation matrix (row 3)
  T1 T2 T3                    # Translation vector
  ```

#### Data Files

- **Target Files (.XXX_targets):** Text files containing detected particle information.
  ```
  # Example target file structure
  5         # Number of targets
  x1 y1 n1  # x-position, y-position, intensity for target 1
  x2 y2 n2  # x-position, y-position, intensity for target 2
  ...
  ```

- **Correspondence Files (.XXX_corres):** Text files containing correspondence information.
  ```
  # Example correspondence file structure
  4                 # Number of particles
  p1 n1 i11 i12 ... # Particle ID, number of cameras, camera indices
  p2 n2 i21 i22 ... # For particle 2
  ...
  ```

- **Tracking Files (.XXX_ptv):** Text files containing tracking information.
  ```
  # Example tracking file structure
  3                    # Number of links
  p1_prev p1_next      # Link from particle 1_prev to particle 1_next
  p2_prev p2_next      # Link from particle 2_prev to particle 2_next
  ...
  ```

#### Output Formats

- **Position Data (.txt, .csv):** Simple, human-readable format for track data.
  ```
  # Example position data structure (text format)
  frame_id particle_id x y z  # Header
  1 1 x11 y11 z11            # Frame 1, Particle 1
  1 2 x12 y12 z12            # Frame 1, Particle 2
  ...
  ```

- **Trajectory Data (.trk, .h5):** Files containing complete particle trajectories.
  ```
  # Example trajectory data structure (text format)
  trajectory_id num_points   # Header for trajectory
  frame_1 x1 y1 z1           # Position at frame 1
  frame_2 x2 y2 z2           # Position at frame 2
  ...
  ```

### Command Line Interface

While PyPTV primarily uses a GUI, some operations can be performed via command-line tools:

```bash
# Launch PyPTV
python -m pyptv [options]

# Run specific pyptv scripts
python -m pyptv.script_name [arguments]

# Examples (actual commands may vary):
python -m pyptv.calibrate --input cal_images/ --output cal_params/
python -m pyptv.track --input detected/ --output tracks/ --params tracking_params.yml
```

### Configuration Parameters Reference

This section provides a reference for the various parameters used in PyPTV:

#### Camera Parameters

- **Image Name Format:** The naming convention for image files (e.g., "cam%d.%d").
- **Image Size:** Width and height of the camera images in pixels.
- **Calibration Method:** The method used for calibration (e.g., DLT, Tsai).
- **Distortion Model:** The lens distortion model used (e.g., radial-tangential).

#### Particle Detection Parameters

- **Intensity Threshold:** Minimum pixel intensity for particle detection.
- **Size Range:** Minimum and maximum particle size in pixels.
- **Subpixel Method:** Method for refining particle positions (e.g., centroid, Gaussian).
- **Connectivity:** Pixel connectivity for connected-component labeling (4 or 8).

#### Correspondence Parameters

- **Epipolar Distance:** Maximum allowed distance between a target and the epipolar line.
- **Minimum Cameras:** Minimum number of cameras in which a particle must be visible.
- **Matching Method:** Algorithm used for correspondence matching.
- **Triangulation Method:** Method used for triangulating 3D positions.

#### Tracking Parameters

- **Search Radius:** Maximum distance a particle can travel between frames.
- **Prediction Method:** Method for predicting particle positions (e.g., constant position, velocity).
- **Minimum Track Length:** Minimum length (in frames) for a valid track.
- **Maximum Velocity:** Maximum allowed particle velocity (if used).
- **Gap Closing:** Parameters for connecting tracks across detection gaps.

### Recommended Reading

For users seeking a deeper understanding of PTV techniques and applications:

#### Foundational Papers

1. Dracos, T. (1996). "Three-Dimensional Velocity and Vorticity Measuring and Image Analysis Techniques."

2. Maas, H. G., Gruen, A., & Papantoniou, D. (1993). "Particle tracking velocimetry in three-dimensional flows."

3. Malik, N. A., Dracos, T., & Papantoniou, D. A. (1993). "Particle tracking velocimetry in three-dimensional flows."

#### Advanced Topics

1. Schanz, D., Gesemann, S., & Schröder, A. (2016). "Shake-The-Box: Lagrangian particle tracking at high particle image densities."

2. Ouellette, N. T., Xu, H., & Bodenschatz, E. (2006). "A quantitative study of three-dimensional Lagrangian particle tracking algorithms."

3. Fuchs, T., Hain, R., & Kähler, C. J. (2016). "Non-iterative double-frame 2D/3D particle tracking velocimetry."

4. Kreizer, M., Ratner, D., & Liberzon, A. (2010). "Real-time image processing for particle tracking velocimetry."

5. Lüthi, B., Tsinober, A., & Kinzelbach, W. (2005). "Lagrangian measurement of vorticity dynamics in turbulent flow."

### Online Resources

1. **OpenPTV Website:** [http://www.openptv.net/](http://www.openptv.net/) (if available)

2. **GitHub Repositories:**
   - PyPTV: [https://github.com/alexlib/pyptv](https://github.com/alexlib/pyptv)
   - OpenPTV C Library: [https://github.com/alexlib/openptv](https://github.com/alexlib/openptv)

3. **Documentation:**
   - ReadTheDocs: [https://openptv-python.readthedocs.io/](https://openptv-python.readthedocs.io/) (if available)

4. **Discussion Forums:**
   - GitHub Issues: [https://github.com/alexlib/pyptv/issues](https://github.com/alexlib/pyptv/issues)

5. **Related Tools:**
   - ParaView (for visualization): [https://www.paraview.org/](https://www.paraview.org/)
   - OpenCV (for image processing): [https://opencv.org/](https://opencv.org/)

