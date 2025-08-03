import sys
import os
from pathlib import Path
from pyptv.experiment import Experiment

def main():
    if len(sys.argv) != 2:
        print("Usage: python legacy_parameters_to_yaml.py <directory_path>")
        sys.exit(1)

    directory_path = sys.argv[1]
    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory.")
        sys.exit(1)

    # Initialize Experiment
    exp = Experiment()
    exp.populate_runs(Path(directory_path))

    # Prepare list of YAML files
    yaml_files = []
    # List all YAML files in the directory
    for file in os.listdir(directory_path):
        if file.endswith(".yaml") or file.endswith(".yml"):
            yaml_files.append(file)  # Store without extension

    # List all parameter names in the experiment
    param_names = [param.yaml_path.name for param in exp.paramsets]
    
    print(yaml_files)
    print(param_names)


    # Compare parameter names to YAML files (without extension)
    # yaml_basenames = [os.path.splitext(f)[0] for f in yaml_files]
    missing_in_yaml = [p for p in param_names if p not in yaml_files]
    extra_yaml = [y for y in yaml_files if y not in param_names]

    print("\nParameters missing YAML files:", missing_in_yaml)
    print("YAML files without matching parameters:", extra_yaml)


if __name__ == "__main__":
    main()