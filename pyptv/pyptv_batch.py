"""PyPTV_BATCH: Batch processing script for 3D-PTV (http://ptv.origo.ethz.ch)

This module provides batch processing capabilities for PyPTV, allowing users to
process sequences of images without the GUI interface.

The script expects:
- A YAML parameter file (e.g., parameters_Run1.yaml)
- img/ directory with image sequences (relative to YAML file location)  
- cal/ directory with calibration files (relative to YAML file location)
- res/ directory (created automatically if missing)

To convert legacy parameters to YAML format:
    python -m pyptv.parameter_util legacy-to-yaml /path/to/parameters/

Example:
    Command line usage:
    >>> python pyptv_batch.py tests/test_cavity/parameters_Run1.yaml 10000 10004

    Python API usage:
    >>> from pyptv.pyptv_batch import main
    >>> main("tests/test_cavity/parameters_Run1.yaml", 10000, 10004)
"""

import logging
from pathlib import Path
import os
import sys
import time
from typing import Union

from pyptv.ptv import py_start_proc_c, py_trackcorr_init, py_sequence_loop
from pyptv.experiment import Experiment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Custom exception for PyPTV batch processing errors."""
    pass


# AttrDict removed - using direct dictionary access with Experiment object


def validate_experiment_setup(yaml_file: Path) -> Path:
    """Validate that the YAML file exists and required directories are available.
    
    Args:
        yaml_file: Path to the YAML parameter file
        
    Returns:
        Path to the experiment directory (parent of YAML file)
        
    Raises:
        ProcessingError: If required files or directories are missing
    """
    if not yaml_file.exists():
        raise ProcessingError(f"YAML parameter file does not exist: {yaml_file}")
    
    if not yaml_file.is_file():
        raise ProcessingError(f"Path is not a file: {yaml_file}")
        
    if not yaml_file.suffix.lower() in ['.yaml', '.yml']:
        raise ProcessingError(f"File must have .yaml or .yml extension: {yaml_file}")
    
    # Get experiment directory (parent of YAML file)
    exp_path = yaml_file.parent
    
    # Check for required subdirectories relative to YAML file location
    # Note: 'res' directory is created automatically if missing
    required_dirs = ["img", "cal"]
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = exp_path / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        raise ProcessingError(
            f"Missing required directories relative to {yaml_file}: {', '.join(missing_dirs)}"
        )
    
    return exp_path


def run_batch(yaml_file: Path, seq_first: int, seq_last: int) -> None:
    """Run batch processing for a sequence of frames.
    
    Args:
        seq_first: First frame number in the sequence
        seq_last: Last frame number in the sequence  
        yaml_file: Path to the YAML parameter file
        
    Raises:
        ProcessingError: If processing fails
    """
    logger.info(f"Starting batch processing: frames {seq_first} to {seq_last}")
    logger.info(f"Using parameter file: {yaml_file}")
    
    # Get experiment directory (parent of YAML file)
    exp_path = yaml_file.parent
    
    # Store original working directory
    original_cwd = Path.cwd()
    
    try:
        # Change to experiment directory
        os.chdir(exp_path)
        
        # Create experiment and load YAML parameters
        experiment = Experiment()
        
        # Load parameters from YAML file
        logger.info(f"Loading parameters from: {yaml_file}")
        experiment.parameter_manager.from_yaml(yaml_file)
        
        
        logger.info(f"Initializing processing with n_cam = {experiment.parameter_manager.n_cam}")
        cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(experiment.parameter_manager)

        # Set sequence parameters
        spar.set_first(seq_first)
        spar.set_last(seq_last)

        # Create a simple object to hold processing parameters for ptv.py functions
        class ProcessingExperiment:
            def __init__(self, experiment, cpar, spar, vpar, track_par, tpar, cals, epar):
                self.parameter_manager = experiment.parameter_manager
                self.cpar = cpar
                self.spar = spar
                self.vpar = vpar
                self.track_par = track_par
                self.tpar = tpar
                self.cals = cals
                self.epar = epar
                self.n_cams = experiment.parameter_manager.n_cam  # Global number of cameras
                # Initialize attributes that may be set during processing
                self.detections = []
                self.corrected = []
        
        proc_exp = ProcessingExperiment(experiment, cpar, spar, vpar, track_par, tpar, cals, epar)

        # Run processing
        logger.info("Running sequence loop...")
        py_sequence_loop(proc_exp)
        
        logger.info("Initializing tracker...")
        tracker = py_trackcorr_init(proc_exp)
        
        logger.info("Running tracking...")
        tracker.full_forward()
        
        logger.info("Batch processing completed successfully")
        
    except Exception as e:
        raise ProcessingError(f"Batch processing failed: {e}")
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


def main(
    yaml_file: Union[str, Path], 
    first: Union[str, int], 
    last: Union[str, int], 
    repetitions: int = 1
) -> None:
    """Run PyPTV batch processing.
    
    Args:
        yaml_file: Path to the YAML parameter file (e.g., parameters_Run1.yaml)
        first: First frame number in the sequence
        last: Last frame number in the sequence  
        repetitions: Number of times to repeat the processing (default: 1)
        
    Raises:
        ProcessingError: If processing fails
        ValueError: If parameters are invalid
        
    Note:
        If you have legacy .par files, convert them first using:
        python -m pyptv.parameter_util legacy-to-yaml /path/to/parameters/
    """
    start_time = time.time()
    
    try:
        # Validate and convert parameters
        yaml_file = Path(yaml_file).resolve()
        seq_first = int(first)
        seq_last = int(last)
        
        if seq_first > seq_last:
            raise ValueError(f"First frame ({seq_first}) must be <= last frame ({seq_last})")
        
        if repetitions < 1:
            raise ValueError(f"Repetitions must be >= 1, got {repetitions}")
            
        logger.info(f"Starting batch processing with YAML file: {yaml_file}")
        logger.info(f"Frame range: {seq_first} to {seq_last}")
        logger.info(f"Repetitions: {repetitions}")
        
        # Validate YAML file and experiment setup
        exp_path = validate_experiment_setup(yaml_file)
        logger.info(f"Experiment directory: {exp_path}")
        
        # Create results directory if it doesn't exist
        res_path = exp_path / "res"
        if not res_path.exists():
            logger.info("Creating 'res' directory")
            res_path.mkdir(parents=True, exist_ok=True)
        
        # Run processing for specified repetitions
        for i in range(repetitions):
            if repetitions > 1:
                logger.info(f"Starting repetition {i + 1} of {repetitions}")
            
            run_batch(yaml_file, seq_first, seq_last)
            
        elapsed_time = time.time() - start_time
        logger.info(f"Total processing time: {elapsed_time:.2f} seconds")
        
    except (ValueError, ProcessingError) as e:
        logger.error(f"Processing failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
        raise ProcessingError(f"Unexpected error: {e}")


def parse_command_line_args() -> tuple[Path, int, int]:
    """Parse and validate command line arguments.
    
    Returns:
        Tuple of (yaml_file_path, first_frame, last_frame)
        
    Raises:
        ValueError: If arguments are invalid
    """
    if len(sys.argv) < 4:
        logger.warning("Insufficient command line arguments, using default test values")
        logger.info("Usage: python pyptv_batch.py <yaml_file> <first_frame> <last_frame>")
        
        # Default values for testing
        yaml_file = Path("tests/test_cavity/parameters_Run1.yaml").resolve()
        first_frame = 10000
        last_frame = 10004
        
        if not yaml_file.exists():
            raise ValueError(
                f"Default test YAML file not found: {yaml_file}. "
                "Please provide valid command line arguments."
            )
    else:
        try:
            yaml_file = Path(sys.argv[1]).resolve()
            first_frame = int(sys.argv[2])
            last_frame = int(sys.argv[3])
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid command line arguments: {e}")
    
    return yaml_file, first_frame, last_frame


if __name__ == "__main__":
    """Entry point for command line execution.
    
    Command line usage:
        python pyptv_batch.py <yaml_file> <first_frame> <last_frame>
        
    Example:
        python pyptv_batch.py tests/test_cavity/parameters_Run1.yaml 10000 10004
    
    Python API usage:
        from pyptv.pyptv_batch import main
        main("tests/test_cavity/parameters_Run1.yaml", 10000, 10004)
    """
    try:
        logger.info("Starting PyPTV batch processing")
        logger.info(f"Command line arguments: {sys.argv}")
        
        yaml_file, first_frame, last_frame = parse_command_line_args()
        main(yaml_file, first_frame, last_frame)
        
        logger.info("Batch processing completed successfully")
        
    except (ValueError, ProcessingError) as e:
        logger.error(f"Batch processing failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)