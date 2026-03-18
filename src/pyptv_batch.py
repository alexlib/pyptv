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

from pathlib import Path
import os
import sys
import time
from typing import Union

from pyptv.ptv import py_start_proc_c, py_trackcorr_init, py_sequence_loop, generate_short_file_bases
from pyptv.experiment import Experiment



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
    # required_dirs = ["img", "cal"]
    # missing_dirs = []
    
    # for dir_name in required_dirs:
    #     dir_path = exp_path / dir_name
    #     if not dir_path.exists():
    #         missing_dirs.append(dir_name)
    
    # if missing_dirs:
    #     raise ProcessingError(
    #         f"Missing required directories relative to {yaml_file}: {', '.join(missing_dirs)}"
    #     )
    
    return exp_path


def run_batch(yaml_file: Path, seq_first: int, seq_last: int, mode: str = "both") -> None:
    """Run batch processing for a sequence of frames.
    
    Args:
        seq_first: First frame number in the sequence
        seq_last: Last frame number in the sequence  
        yaml_file: Path to the YAML parameter file
        
    Raises:
        ProcessingError: If processing fails
    """
    print(f"Starting batch processing: frames {seq_first} to {seq_last}")
    print(f"Using parameter file: {yaml_file}")

    # Validate experiment setup and get experiment directory
    exp_path = validate_experiment_setup(yaml_file)

    # Store original working directory
    original_cwd = Path.cwd()

    try:
        # Change to experiment directory
        os.chdir(exp_path)

        # Create experiment and load YAML parameters
        experiment = Experiment()

        # Load parameters from YAML file
        print(f"Loading parameters from: {yaml_file}")
        experiment.pm.from_yaml(yaml_file)

        print(f"Initializing processing with num_cams = {experiment.pm.num_cams}")
        cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(experiment.pm)

        # Set sequence parameters
        spar.set_first(seq_first)
        spar.set_last(seq_last)

        # Create a simple object to hold processing parameters for ptv.py functions
        class ProcessingExperiment:
            def __init__(self, experiment, cpar, spar, vpar, track_par, tpar, cals, epar):
                self.pm = experiment.pm
                self.cpar = cpar
                self.spar = spar
                self.vpar = vpar
                self.track_par = track_par
                self.tpar = tpar
                self.cals = cals
                self.epar = epar
                self.num_cams = experiment.pm.num_cams  # Global number of cameras
                # Initialize attributes that may be set during processing
                self.detections = []
                self.corrected = []

        proc_exp = ProcessingExperiment(experiment, cpar, spar, vpar, track_par, tpar, cals, epar)

        # Centralized: get target_filenames from ParameterManager
        proc_exp.target_filenames = experiment.pm.get_target_filenames()

        # Run processing according to mode
        if mode == "both":
            print("Running sequence loop...")
            py_sequence_loop(proc_exp)
            print("Initializing tracker...")
            tracker = py_trackcorr_init(proc_exp)
            print("Running tracking...")
            tracker.full_forward()
        elif mode == "sequence":
            print("Running sequence loop only...")
            py_sequence_loop(proc_exp)
        elif mode == "tracking":
            print("Initializing tracker only (skipping sequence)...")
            tracker = py_trackcorr_init(proc_exp)
            print("Running tracking only...")
            tracker.full_forward()
        else:
            raise ProcessingError(f"Unknown mode: {mode}. Use 'both', 'sequence', or 'tracking'.")

        print("Batch processing completed successfully")

    except Exception as e:
        raise ProcessingError(f"Batch processing failed: {e}")
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


def main(
    yaml_file: Union[str, Path], 
    first: Union[str, int], 
    last: Union[str, int], 
    repetitions: int = 1,
    mode: str = "both"
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

        exp_path = yaml_file.parent
        
        if seq_first > seq_last:
            raise ValueError(f"First frame ({seq_first}) must be <= last frame ({seq_last})")
        
        if repetitions < 1:
            raise ValueError(f"Repetitions must be >= 1, got {repetitions}")
            
        print(f"Starting batch processing with YAML file: {yaml_file}")
        print(f"Frame range: {seq_first} to {seq_last}")
        print(f"Repetitions: {repetitions}")
        # Validate YAML file and experiment setup
        # exp_path = validate_experiment_setup(yaml_file)
        print(f"Experiment directory: {exp_path}")
        # Create results directory if it doesn't exist
        res_path = exp_path / "res"
        if not res_path.exists():
            print("Creating 'res' directory")
            res_path.mkdir(parents=True, exist_ok=True)
        
        # Run processing for specified repetitions
        for i in range(repetitions):
            if repetitions > 1:
                print(f"Starting repetition {i + 1} of {repetitions}")
            run_batch(yaml_file, seq_first, seq_last, mode=mode)
        elapsed_time = time.time() - start_time
        print(f"Total processing time: {elapsed_time:.2f} seconds")
        
    except (ValueError, ProcessingError) as e:
        print(f"Processing failed: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error during processing: {e}")
        raise ProcessingError(f"Unexpected error: {e}")


def parse_command_line_args() -> tuple[Path, int, int]:
    """Parse and validate command line arguments.
    
    Returns:
        Tuple of (yaml_file_path, first_frame, last_frame)
        
    Raises:
        ValueError: If arguments are invalid
    """
    import argparse
    parser = argparse.ArgumentParser(description="PyPTV batch processing")
    parser.add_argument("yaml_file", type=str, help="YAML parameter file")
    parser.add_argument("first_frame", type=int, nargs="?", help="First frame number")
    parser.add_argument("last_frame", type=int, nargs="?", help="Last frame number")
    parser.add_argument("--mode", choices=["both", "sequence", "tracking"], default="both", help="Which steps to run: both (default), sequence, or tracking")
    args = parser.parse_args()

    yaml_file = Path(args.yaml_file).resolve()
    from pyptv.parameter_manager import ParameterManager
    pm = ParameterManager()
    pm.from_yaml(yaml_file)

    if args.first_frame is not None:
        first_frame = args.first_frame
    else:
        first_frame = pm.parameters.get("sequence").get("first")

    if args.last_frame is not None:
        last_frame = args.last_frame
    else:
        last_frame = pm.parameters.get("sequence").get("last")

    mode = args.mode

    return yaml_file, first_frame, last_frame, mode


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
        print("Starting batch processing")
        print(f"Command line arguments: {sys.argv}")
        
        yaml_file, first_frame, last_frame, mode = parse_command_line_args()
        main(yaml_file, first_frame, last_frame, mode=mode)
        
        print("Batch processing completed successfully")
        
    except (ValueError, ProcessingError) as e:
        print(f"Batch processing failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)