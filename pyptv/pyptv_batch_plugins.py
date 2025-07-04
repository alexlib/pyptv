"""PyPTV_BATCH: Batch processing script with plugin support

Script for PyPTV experiments that have been set up using the GUI.
Supports custom tracking and sequence plugins.

Example:
    python pyptv_batch_plugins.py tests/test_splitter 10000 10004 --tracking splitter --sequence splitter
"""

import logging
from pathlib import Path
import os
import sys
import json
import importlib

from pyptv.ptv import py_start_proc_c
from pyptv.experiment import Experiment

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_plugins_config(exp_path: Path):
    """Load available plugins from experiment parameters (YAML) with fallback to plugins.json"""
    from pyptv.experiment import Experiment
    
    try:
        # Primary source: YAML parameters
        experiment = Experiment()
        experiment.populate_runs(exp_path)
        if experiment.nParamsets() > 0:
            experiment.setActive(0)  # Use first parameter set
            plugins_params = experiment.get_parameter('plugins')
            if plugins_params is not None:
                return {
                    "tracking": plugins_params.get('available_tracking', ['default']),
                    "sequence": plugins_params.get('available_sequence', ['default'])
                }
    except Exception as e:
        print(f"Error loading plugins from YAML: {e}")
    
    # Fallback to plugins.json for backward compatibility (deprecated)
    plugins_file = exp_path / "plugins.json"
    if plugins_file.exists():
        logger.warning("Using deprecated plugins.json - please migrate to YAML parameters")
        with open(plugins_file, 'r') as f:
            return json.load(f)
    
    return {"tracking": ["default"], "sequence": ["default"]}

def run_batch(exp_path: Path, seq_first: int, seq_last: int, 
              tracking_plugin: str = "default", sequence_plugin: str = "default"):
    """Run batch processing with plugins"""
    
    # Change to experiment directory
    original_cwd = Path.cwd()
    os.chdir(exp_path)
    
    try:
        # Create experiment and load parameters
        experiment = Experiment()
        experiment.populate_runs(exp_path)
        
        logger.info(f"Processing frames {seq_first}-{seq_last} with {experiment.get_n_cam()} cameras")
        logger.info(f"Using plugins: tracking={tracking_plugin}, sequence={sequence_plugin}")
        
        # Initialize PyPTV with parameter manager
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
                self.n_cams = experiment.get_n_cam()
                self.exp_path = str(exp_path.absolute())
                self.detections = []
                self.corrected = []
        
        exp_config = ProcessingExperiment(experiment, cpar, spar, vpar, track_par, tpar, cals, epar)
        
        # Add plugins directory to path we're inside exp_path
        plugins_dir = Path.cwd() / "plugins"
        if str(plugins_dir) not in sys.path:
            sys.path.insert(0, str(plugins_dir.absolute()))

        try:
            seq_plugin = importlib.import_module(sequence_plugin)
        except ImportError as e:
            print(f"Error loading {sequence_plugin}: {e}")
            print("Check for missing packages or syntax errors.")
            return

        # Check if the plugin has a Sequence class
        if hasattr(seq_plugin, "Sequence"):
            print(f"Running sequence plugin: {sequence_plugin}")
            try:
                # Create a Sequence instance and run it
                sequence = seq_plugin.Sequence(exp = exp_config)
                sequence.do_sequence()
            except Exception as e:
                print(f"Error running sequence plugin: {e}")
                return
            
        try:
            track_plugin = importlib.import_module(tracking_plugin)
        except ImportError as e:
            print(f"Error loading {tracking_plugin}: {e}")
            print("Check for missing packages or syntax errors.")
            return
                
        # Run tracking
        if track_plugin:
            logger.info(f"Running tracking plugin: {tracking_plugin}")
            tracker = track_plugin.Tracking(exp=exp_config)
            tracker.do_tracking()
        else:
            logger.error(f"Tracking plugin {tracking_plugin} not found or not implemented.")
            return
            
        logger.info("Batch processing completed successfully")
        
    finally:
        os.chdir(original_cwd)


def main():
    """Main entry point"""
    if len(sys.argv) < 4:
        print("Usage: python pyptv_batch_plugins.py <exp_path> <first_frame> <last_frame>")
        print("Example: python pyptv_batch_plugins.py tests/test_splitter 1000001 1000005")
        return
    
    exp_path = Path(sys.argv[1])
    first_frame = int(sys.argv[2])
    last_frame = int(sys.argv[3])

    
    # Show available plugins
    plugins_config = load_plugins_config(exp_path)
    logger.info(f"Available tracking plugins: {plugins_config.get('tracking', ['default'])}")
    logger.info(f"Available sequence plugins: {plugins_config.get('sequence', ['default'])}")
    
    tracking_plugin = plugins_config.get('tracking', ['default'])[0]  # Default to first available
    sequence_plugin = plugins_config.get('sequence', ['default'])[0]  # Default to first available
    

    run_batch(exp_path, first_frame, last_frame, tracking_plugin, sequence_plugin)


if __name__ == "__main__":
    main()
