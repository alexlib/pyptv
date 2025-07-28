"""PyPTV_BATCH: Batch processing script with plugin support

Script for PyPTV experiments that have been set up using the GUI.
Supports custom tracking and sequence plugins.

Example:
    python pyptv_batch_plugins.py tests/test_splitter 10000 10004 --tracking splitter --sequence splitter
"""

from pathlib import Path
import os
import sys
import json
import importlib

from pyptv.ptv import generate_short_file_bases, py_start_proc_c
from pyptv.experiment import Experiment


def load_plugins_config(exp_path: Path):
    """Load available plugins from experiment parameters (YAML) with fallback to plugins.json"""
    from pyptv.experiment import Experiment
    try:
        experiment = Experiment()
        experiment.pm.from_yaml(exp_path)  # Corrected to use exp_path
        plugins_params = experiment.pm.parameters.get('plugins', None)
        if plugins_params is not None:
            return {
                "tracking": plugins_params.get('available_tracking', ['default']),
                "sequence": plugins_params.get('available_sequence', ['default'])
            }
    except Exception as e:
        print(f"Error loading plugins from YAML: {e}")
    # Fallback to plugins.json for backward compatibility (deprecated)
    plugins_file = exp_path.parent / "plugins.json"  # Corrected to use exp_path
    if plugins_file.exists():
        print("WARNING: Using deprecated plugins.json - please migrate to YAML parameters")
        with open(plugins_file, 'r') as f:
            return json.load(f)
    return {"tracking": ["default"], "sequence": ["default"]}

def run_batch(yaml_file: Path, seq_first: int, seq_last: int, 
              tracking_plugin: str = "default", sequence_plugin: str = "default", mode: str = "both"):
    """Run batch processing with plugins, supporting modular mode (both, sequence, tracking)"""
    original_cwd = Path.cwd()
    exp_path = yaml_file.parent
    os.chdir(exp_path)
    experiment = Experiment()
    experiment.pm.from_yaml(yaml_file)
    print(f"Processing frames {seq_first}-{seq_last} with {experiment.pm.num_cams} cameras")
    print(f"Using plugins: tracking={tracking_plugin}, sequence={sequence_plugin}")
    print(f"Mode: {mode}")
    cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(experiment.pm)
    spar.set_first(seq_first)
    spar.set_last(seq_last)
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
            self.exp_path = str(exp_path.absolute())
            self.detections = []
            self.corrected = []
    exp_config = ProcessingExperiment(experiment, cpar, spar, vpar, track_par, tpar, cals, epar)

    # Centralized: get target_filenames from ParameterManager
    exp_config.target_filenames = experiment.pm.get_target_filenames()

    plugins_dir = Path.cwd() / "plugins"
    print(f"[DEBUG] Plugins directory: {plugins_dir}")
    if str(plugins_dir) not in sys.path:
        sys.path.insert(0, str(plugins_dir.absolute()))
        print(f"[DEBUG] Added plugins directory to sys.path: {plugins_dir}")
    # Patch: Ensure output files are written to 'res' directory for test_splitter
    res_dir = Path("res")
    if not res_dir.exists():
        res_dir.mkdir(exist_ok=True)
    try:
        if mode in ("both", "sequence"):
            seq_plugin = importlib.import_module(sequence_plugin)
            if hasattr(seq_plugin, "Sequence"):
                print(f"Running sequence plugin: {sequence_plugin}")
                try:
                    sequence = seq_plugin.Sequence(exp=exp_config)
                    sequence.do_sequence()
                except Exception as e:
                    print(f"Error running sequence plugin: {e}")
                    os.chdir(original_cwd)
                    return
        if mode in ("both", "tracking"):
            try:
                track_plugin = importlib.import_module(tracking_plugin)
                print(f"[DEBUG] Loaded tracking plugin: {track_plugin}")
                print(f"Running tracking plugin: {tracking_plugin}")
                tracker = track_plugin.Tracking(exp=exp_config)
                tracker.do_tracking()
            except Exception as e:
                print(f"ERROR: Tracking plugin {tracking_plugin} not found or not implemented. Exception: {e}")
                os.chdir(original_cwd)
                return
        print("Batch processing completed successfully")
    except ImportError as e:
        print(f"Error loading plugin: {e}")
        print("Check for missing packages or syntax errors.")
    finally:
        os.chdir(original_cwd)


def main():
    """Main entry point with argparse and --mode support"""
    import argparse
    parser = argparse.ArgumentParser(
        description="PyPTV batch processing with plugins. Supports running only sequence, only tracking, or both."
    )
    parser.add_argument("yaml_file", type=str, help="Path to YAML parameter file.")
    parser.add_argument("first_frame", type=int, help="First frame number.")
    parser.add_argument("last_frame", type=int, help="Last frame number.")
    parser.add_argument(
        "--mode", type=str, default="both", choices=["both", "sequence", "tracking"],
        help="Which steps to run: both (default), sequence, or tracking."
    )
    args = parser.parse_args()
    yaml_file = Path(args.yaml_file).resolve()
    first_frame = args.first_frame
    last_frame = args.last_frame
    mode = args.mode
    # Show available plugins
    plugins_config = load_plugins_config(yaml_file)
    print(f"Available tracking plugins: {plugins_config.get('tracking', ['default'])}")
    print(f"Available sequence plugins: {plugins_config.get('sequence', ['default'])}")
    tracking_plugin = plugins_config.get('tracking', ['default'])[0]
    sequence_plugin = plugins_config.get('sequence', ['default'])[0]
    run_batch(yaml_file, first_frame, last_frame, tracking_plugin, sequence_plugin, mode)


if __name__ == "__main__":
    main()
