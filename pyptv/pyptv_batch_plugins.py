"""PyPTV_BATCH: Batch processing script with plugin support

Simple batch processing for PyPTV experiments that have been set up using the GUI.
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

from pyptv.ptv import py_start_proc_c, py_trackcorr_init, py_sequence_loop

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AttrDict(dict):
    """Dictionary that allows attribute-style access to its items."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


def load_plugins_config(exp_path: Path):
    """Load available plugins from plugins.json"""
    plugins_file = exp_path / "plugins.json"
    if plugins_file.exists():
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
        # Get number of cameras from ptv.par
        with open("parameters/ptv.par", "r") as f:
            n_cams = int(f.readline().strip())
        
        logger.info(f"Processing frames {seq_first}-{seq_last} with {n_cams} cameras")
        logger.info(f"Using plugins: tracking={tracking_plugin}, sequence={sequence_plugin}")
        
        # Initialize PyPTV
        cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(n_cams=n_cams)
        # Set sequence parameters
        spar.set_first(seq_first)
        spar.set_last(seq_last)
        

        # Create config object
        exp_config = AttrDict({
            "n_cams": n_cams,
            "cpar": cpar, "spar": spar, "vpar": vpar,
            "track_par": track_par, "tpar": tpar, "cals": cals,
            "epar": epar, "exp_path": str(exp_path.absolute()),
        })
        
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
