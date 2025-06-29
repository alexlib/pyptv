"""PyPTV_BATCH: Batch processing script for 3D-PTV (http://ptv.origo.ethz.ch)

This module provides batch processing capabilities for PyPTV, allowing users to
process sequences of images without the GUI interface.

Example:
    Command line usage:
    >>> python pyptv_batch.py experiments/exp1 10001 10022

    Python API usage:
    >>> from pyptv.pyptv_batch import main
    >>> main("experiments/exp1", 10001, 10022)

The script expects the experiment directory to contain the standard OpenPTV
folder structure with /parameters, /img, /cal, and /res directories.
"""

import logging
from pathlib import Path
import os
import sys
import time
from typing import Union

from pyptv.ptv import py_start_proc_c, py_trackcorr_init, py_sequence_loop
from pyptv.parameter_manager import ParameterManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Custom exception for PyPTV batch processing errors."""
    pass


class AttrDict(dict):
    """Dictionary that allows attribute-style access to its items."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


def validate_experiment_directory(exp_path: Path) -> None:
    """Validate that the experiment directory has the required structure.
    
    Args:
        exp_path: Path to the experiment directory
        
    Raises:
        ProcessingError: If required directories or files are missing
    """
    if not exp_path.exists():
        raise ProcessingError(f"Experiment directory does not exist: {exp_path}")
    
    if not exp_path.is_dir():
        raise ProcessingError(f"Path is not a directory: {exp_path}")
    
    # Check for required subdirectories
    required_dirs = ["parameters", "img", "cal"]
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = exp_path / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        raise ProcessingError(
            f"Missing required directories in {exp_path}: {', '.join(missing_dirs)}"
        )
    
    # Check for required parameter file
    ptv_par_file = exp_path / "parameters" / "ptv.par"
    if not ptv_par_file.exists():
        raise ProcessingError(f"Required file not found: {ptv_par_file}")


def run_batch(seq_first: int, seq_last: int, exp_path: Path) -> None:
    """Run batch processing for a sequence of frames.
    
    Args:
        seq_first: First frame number in the sequence
        seq_last: Last frame number in the sequence  
        exp_path: Path to the experiment directory
        
    Raises:
        ProcessingError: If processing fails
    """
    logger.info(f"Starting batch processing: frames {seq_first} to {seq_last}")
    
    try:
        # Change to experiment directory
        original_cwd = Path.cwd()
        os.chdir(exp_path)
        
        pm = ParameterManager()
        pm.from_directory(exp_path / "parameters")
        
        # Initialize processing parameters
        cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(pm.parameters)

        # Set sequence parameters
        spar.set_first(seq_first)
        spar.set_last(seq_last)

        # Create experiment configuration
        exp_config = AttrDict({
            "cpar": cpar,
            "spar": spar,
            "vpar": vpar,
            "track_par": track_par,
            "tpar": tpar,
            "cals": cals,
            "epar": epar,
            "n_cams": pm.get_parameter('ptv')['n_img'],
            "pm": pm,
        })

        # Run processing
        py_sequence_loop(exp_config)
        tracker = py_trackcorr_init(exp_config)
        tracker.full_forward()
        
        logger.info("Batch processing completed successfully")
        
    except Exception as e:
        raise ProcessingError(f"Batch processing failed: {e}")
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


def main(
    exp_path: Union[str, Path], 
    first: Union[str, int], 
    last: Union[str, int], 
    repetitions: int = 1
) -> None:
    """Run PyPTV batch processing.
    
    Args:
        exp_path: Path to the experiment directory containing the required
                 folder structure (/parameters, /img, /cal, /res)
        first: First frame number in the sequence
        last: Last frame number in the sequence  
        repetitions: Number of times to repeat the processing (default: 1)
        
    Raises:
        ProcessingError: If processing fails
        ValueError: If parameters are invalid
    """
    start_time = time.time()
    
    try:
        # Validate and convert parameters
        exp_path = Path(exp_path).resolve()
        seq_first = int(first)
        seq_last = int(last)
        
        if seq_first > seq_last:
            raise ValueError(f"First frame ({seq_first}) must be <= last frame ({seq_last})")
        
        if repetitions < 1:
            raise ValueError(f"Repetitions must be >= 1, got {repetitions}")
            
        logger.info(f"Starting batch processing in directory: {exp_path}")
        logger.info(f"Frame range: {seq_first} to {seq_last}")
        logger.info(f"Repetitions: {repetitions}")
        
        # Validate experiment directory structure
        validate_experiment_directory(exp_path)
        
        # Create results directory if it doesn't exist
        res_path = exp_path / "res"
        if not res_path.exists():
            logger.info("Creating 'res' directory")
            res_path.mkdir(parents=True, exist_ok=True)
        
        # Run processing for specified repetitions
        for i in range(repetitions):
            if repetitions > 1:
                logger.info(f"Starting repetition {i + 1} of {repetitions}")
            
            run_batch(seq_first, seq_last, exp_path)
            
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
        Tuple of (experiment_path, first_frame, last_frame)
        
    Raises:
        ValueError: If arguments are invalid
    """
    if len(sys.argv) < 4:
        logger.warning("Insufficient command line arguments, using default test values")
        logger.info("Usage: python pyptv_batch.py <exp_path> <first_frame> <last_frame>")
        
        # Default values for testing
        exp_path = Path("tests/test_cavity").resolve()
        first_frame = 10000
        last_frame = 10004
        
        if not exp_path.exists():
            raise ValueError(
                f"Default test directory not found: {exp_path}. "
                "Please provide valid command line arguments."
            )
    else:
        try:
            exp_path = Path(sys.argv[1]).resolve()
            first_frame = int(sys.argv[2])
            last_frame = int(sys.argv[3])
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid command line arguments: {e}")
    
    return exp_path, first_frame, last_frame


if __name__ == "__main__":
    """Entry point for command line execution.
    
    Command line usage:
        python pyptv_batch.py <exp_path> <first_frame> <last_frame>
        
    Example:
        python pyptv_batch.py ~/test_cavity 10000 10004
    
    Python API usage:
        from pyptv.pyptv_batch import main
        main("experiments/exp1", 10001, 10022)
    """
    try:
        logger.info("Starting PyPTV batch processing")
        logger.info(f"Command line arguments: {sys.argv}")
        
        exp_path, first_frame, last_frame = parse_command_line_args()
        main(exp_path, first_frame, last_frame)
        
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