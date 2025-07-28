"""PyPTV_BATCH_PARALLEL: Parallel batch processing for 3D-PTV (http://ptv.origo.ethz.ch)

This module provides parallel batch processing capabilities for PyPTV, allowing users to
process sequences of images without the GUI interface using multiple CPU cores for improved
performance. The frame range is split into chunks that are processed concurrently.

Example:
    Command line usage:
    >>> python pyptv_batch_parallel.py experiments/exp1 10001 11001 4

    Python API usage:
    >>> from pyptv.pyptv_batch_parallel import main
    >>> main("experiments/exp1", 10001, 11001, n_processes=4)

The script expects the experiment directory to contain the standard OpenPTV
folder structure with /parameters, /img, /cal, and /res directories.

Notes:
    - Only the sequence step (detection/correspondence) is parallelized
    - Tracking is not parallelized in this implementation
    - Choose n_processes based on available CPU cores
    - Each process operates on a separate chunk of frames
"""

import logging
from pathlib import Path
import os
import sys
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Union, List, Tuple

from pyptv.ptv import py_start_proc_c, py_sequence_loop, generate_short_file_bases
from pyptv.experiment import Experiment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """Custom exception for PyPTV parallel batch processing errors."""
    pass


# AttrDict removed - using direct dictionary access with Experiment object

def run_sequence_chunk(yaml_file: Union[str, Path], seq_first: int, seq_last: int) -> Tuple[int, int]:
    """Run sequence processing for a chunk of frames in a separate process.
    
    Args:
        yaml_file: Path to the YAML parameter file
        seq_first: First frame number in the chunk
        seq_last: Last frame number in the chunk
        
    Returns:
        Tuple of (seq_first, seq_last) indicating the processed range
        
    Raises:
        ProcessingError: If processing fails
    """
    logger.info(f"Worker process starting: frames {seq_first} to {seq_last}")
    
    try:
        yaml_file = Path(yaml_file).resolve()
        exp_path = yaml_file.parent
        
        # Store original working directory
        original_cwd = Path.cwd()
        
        # Change to experiment directory
        os.chdir(exp_path)
        
        # Create experiment and load YAML parameters
        experiment = Experiment()
        
        # Load parameters from YAML file
        experiment.pm.from_yaml(yaml_file)
        
        # Initialize processing parameters using the experiment
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
                self.num_cams = experiment.pm.num_cams
                self.detections = []
                self.corrected = []
        
        proc_exp = ProcessingExperiment(experiment, cpar, spar, vpar, track_par, tpar, cals, epar)
        
        
        # Centralized: get target_filenames from ParameterManager
        proc_exp.target_filenames = experiment.pm.get_target_filenames()

        # Run sequence processing
        py_sequence_loop(proc_exp)
        
        # Only run sequence processing in parallel batch
        logger.info(f"Worker process completed: frames {seq_first} to {seq_last}")
        return (seq_first, seq_last)
        
    except Exception as e:
        error_msg = f"Chunk processing failed for frames {seq_first}-{seq_last}: {e}"
        logger.error(error_msg)
        raise ProcessingError(error_msg)
    finally:
        # Restore original working directory
        if 'original_cwd' in locals():
            os.chdir(original_cwd)

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
    required_dirs = ["img", "cal"]  # res is created automatically
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

def chunk_ranges(first: int, last: int, n_chunks: int) -> List[Tuple[int, int]]:
    """Split the frame range into n_chunks as evenly as possible.
    
    Args:
        first: First frame number
        last: Last frame number
        n_chunks: Number of chunks to create
        
    Returns:
        List of tuples containing (start_frame, end_frame) for each chunk
        
    Raises:
        ValueError: If parameters are invalid
    """
    if first > last:
        raise ValueError(f"First frame ({first}) must be <= last frame ({last})")
    
    if n_chunks < 1:
        raise ValueError(f"Number of chunks must be >= 1, got {n_chunks}")
    
    total_frames = last - first + 1
    
    if n_chunks > total_frames:
        logger.warning(
            f"Number of chunks ({n_chunks}) is greater than total frames ({total_frames}). "
            f"Using {total_frames} chunks instead."
        )
        n_chunks = total_frames
    
    chunk_size = total_frames // n_chunks
    remainder = total_frames % n_chunks
    
    ranges = []
    current_start = first
    
    for i in range(n_chunks):
        # Add an extra frame to the first 'remainder' chunks to distribute frames evenly
        current_chunk_size = chunk_size + (1 if i < remainder else 0)
        current_end = current_start + current_chunk_size - 1
        
        ranges.append((current_start, current_end))
        current_start = current_end + 1
    
    return ranges

def main(
    yaml_file: Union[str, Path],
    first: Union[str, int],
    last: Union[str, int],
    n_processes: int = 2,
    mode: str = "both"
) -> None:
    """Run PyPTV parallel batch processing with modular mode support.
    
    Args:
        yaml_file: Path to the YAML parameter file (e.g., parameters_Run1.yaml)
        first: First frame number in the sequence
        last: Last frame number in the sequence
        n_processes: Number of parallel processes to use
        mode: Which steps to run: 'both', 'sequence', or 'tracking'
    Raises:
        ProcessingError: If processing fails
        ValueError: If parameters are invalid
    """
    start_time = time.time()
    try:
        # Validate and convert parameters
        yaml_file = Path(yaml_file).resolve()
        seq_first = int(first)
        seq_last = int(last)
        mode = str(mode).lower()
        if mode not in ("both", "sequence", "tracking"):
            raise ValueError(f"Invalid mode: {mode}. Must be one of: both, sequence, tracking")
        if seq_first > seq_last:
            raise ValueError(f"First frame ({seq_first}) must be <= last frame ({seq_last})")
        # Set default number of processes if not specified
        if n_processes is None:
            n_processes = multiprocessing.cpu_count()
            logger.info(f"Using default number of processes: {n_processes} (CPU count)")
        else:
            n_processes = int(n_processes)
        if n_processes < 1:
            raise ValueError(f"Number of processes must be >= 1, got {n_processes}")
        max_processes = multiprocessing.cpu_count()
        if n_processes > max_processes:
            logger.warning(
                f"Requested {n_processes} processes, but only {max_processes} CPUs available. "
                f"Consider using fewer processes for optimal performance."
            )
        logger.info(f"Starting parallel batch processing with YAML file: {yaml_file}")
        logger.info(f"Frame range: {seq_first} to {seq_last}")
        logger.info(f"Number of processes: {n_processes}")
        logger.info(f"Mode: {mode}")
        # Validate YAML file and experiment setup
        exp_path = validate_experiment_setup(yaml_file)
        logger.info(f"Experiment directory: {exp_path}")
        # Create results directory if it doesn't exist
        res_path = exp_path / "res"
        if not res_path.exists():
            logger.info("Creating 'res' directory")
            res_path.mkdir(parents=True, exist_ok=True)
        # Run sequence step in parallel if requested
        if mode in ("both", "sequence"):
            ranges = chunk_ranges(seq_first, seq_last, n_processes)
            logger.info(f"Frame chunks: {ranges}")
            successful_chunks = 0
            failed_chunks = 0
            with ProcessPoolExecutor(max_workers=n_processes) as executor:
                future_to_range = {
                    executor.submit(run_sequence_chunk, yaml_file, chunk_first, chunk_last): (chunk_first, chunk_last)
                    for chunk_first, chunk_last in ranges
                }
                for future in as_completed(future_to_range):
                    chunk_range = future_to_range[future]
                    try:
                        result = future.result()
                        logger.info(f"✓ Completed chunk: frames {result[0]} to {result[1]}")
                        successful_chunks += 1
                    except Exception as e:
                        logger.error(f"✗ Failed chunk: frames {chunk_range[0]} to {chunk_range[1]} - {e}")
                        failed_chunks += 1
            total_chunks = len(ranges)
            elapsed_time = time.time() - start_time
            logger.info("Parallel sequence processing completed:")
            logger.info(f"  Total chunks: {total_chunks}")
            logger.info(f"  Successful: {successful_chunks}")
            logger.info(f"  Failed: {failed_chunks}")
            logger.info(f"  Total processing time: {elapsed_time:.2f} seconds")
            if failed_chunks > 0:
                raise ProcessingError(f"{failed_chunks} out of {total_chunks} chunks failed")
        # Run tracking step if requested (serial, for now)
        if mode in ("both", "tracking"):
            logger.info("Starting tracking step (serial, not parallelized)")
            try:
                from pyptv.pyptv_batch import run_batch
                run_batch(yaml_file, seq_first, seq_last, mode="tracking")
                logger.info("Tracking step completed successfully.")
            except Exception as e:
                logger.error(f"Tracking step failed: {e}")
                raise ProcessingError(f"Tracking step failed: {e}")
    except (ValueError, ProcessingError) as e:
        logger.error(f"Parallel processing failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during parallel processing: {e}")
        raise ProcessingError(f"Unexpected error: {e}")

def parse_command_line_args():
    """Parse and validate command line arguments for pyptv_batch_parallel.py.
    Returns:
        Tuple of (yaml_file_path, first_frame, last_frame, n_processes, mode)
    Raises:
        ValueError: If arguments are invalid
    """
    import argparse
    parser = argparse.ArgumentParser(
        description="PyPTV parallel batch processing. Supports running only sequence, only tracking, or both."
    )
    parser.add_argument("yaml_file", type=str, help="Path to YAML parameter file.")
    parser.add_argument("first_frame", type=int, help="First frame number.")
    parser.add_argument("last_frame", type=int, help="Last frame number.")
    parser.add_argument("n_processes", type=int, help="Number of parallel processes.")
    parser.add_argument(
        "--mode", type=str, default="both", choices=["both", "sequence", "tracking"],
        help="Which steps to run: both (default), sequence, or tracking."
    )
    args = parser.parse_args()
    yaml_file = Path(args.yaml_file).resolve()
    first_frame = args.first_frame
    last_frame = args.last_frame
    n_processes = args.n_processes
    mode = args.mode
    return yaml_file, first_frame, last_frame, n_processes, mode

if __name__ == "__main__":
    """Entry point for command line execution.
    
    Command line usage:
        python pyptv_batch_parallel.py <yaml_file> <first_frame> <last_frame> <n_processes> [--mode both|sequence|tracking]
    
    Example:
        python pyptv_batch_parallel.py tests/test_cavity/parameters_Run1.yaml 10000 10004 4 --mode both
    
    Python API usage:
        from pyptv.pyptv_batch_parallel import main
        main("tests/test_cavity/parameters_Run1.yaml", 10000, 10004, n_processes=4, mode="both")
    """
    try:
        logger.info("Starting PyPTV parallel batch processing")
        logger.info(f"Command line arguments: {sys.argv}")
        yaml_file, first_frame, last_frame, n_processes, mode = parse_command_line_args()
        main(yaml_file, first_frame, last_frame, n_processes, mode)
        logger.info("Parallel batch processing completed successfully")
    except (ValueError, ProcessingError) as e:
        logger.error(f"Parallel batch processing failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)