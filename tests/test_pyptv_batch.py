import pytest
from pathlib import Path
from pyptv import pyptv_batch
import tempfile
import shutil
import yaml
from scipy.optimize import minimize
import pandas as pd
import io
import sys
import re
import subprocess
import os


def test_pyptv_batch(test_data_dir):
    """Test batch processing with test cavity data using YAML parameters and validate output."""
    test_dir = test_data_dir
    assert test_dir.exists(), f"Test directory {test_dir} not found"

    yaml_file = test_dir / "parameters_Run1.yaml"
    assert yaml_file.exists(), f"YAML parameter file {yaml_file} not found"

    start_frame = 10000
    end_frame = 10004

    try:
        pyptv_batch.main(yaml_file, start_frame, end_frame)
    except Exception as e:
        pytest.fail(f"Batch processing failed: {str(e)}")

    res_dir = test_dir / "res"
    assert res_dir.exists(), "Results directory should be created"

    # Robust check: validate all correspondence files
    for frame in range(start_frame, end_frame + 1):
        corres_file = res_dir / f"rt_is.{frame}"
        assert corres_file.exists(), f"Correspondence file {corres_file} should exist"
        content = corres_file.read_text()
        lines = content.strip().split('\n')
        assert len(lines) > 1, f"Correspondence file {corres_file} should have more than just the count line"
        num_points = int(lines[0])
        assert num_points > 0, f"Frame {frame} should have detected correspondences, got {num_points}"
        assert num_points == len(lines) - 1, f"Number of points should match number of data lines in {corres_file}"

    print(f"Successfully detected correspondences in frames {start_frame} to {end_frame}")


def test_pyptv_batch_with_repetitions(test_data_dir):
    """Test batch processing with multiple repetitions"""
    test_dir = test_data_dir
    yaml_file = test_dir / "parameters_Run1.yaml"
    
    # Test smaller frame range with repetitions
    start_frame = 10000
    end_frame = 10001  # Just 2 frames for speed
    repetitions = 2

    try:
        pyptv_batch.main(yaml_file, start_frame, end_frame, repetitions)
    except Exception as e:
        pytest.fail(f"Batch processing with repetitions failed: {str(e)}")


def test_pyptv_batch_validation_errors():
    """Test that proper validation errors are raised"""
    from pyptv.pyptv_batch import ProcessingError
    
    # Test non-existent YAML file
    with pytest.raises(ProcessingError, match="YAML parameter file does not exist"):
        pyptv_batch.main("nonexistent.yaml", 1, 2)
    
    # Test invalid frame range
    with pytest.raises(ValueError, match="First frame .* must be <= last frame"):
        pyptv_batch.main("any.yaml", 10, 5)  # first > last
    
    # Test invalid repetitions
    with pytest.raises(ValueError, match="Repetitions must be >= 1"):
        pyptv_batch.main("any.yaml", 1, 2, 0)  # repetitions = 0


def test_pyptv_batch_produces_results(test_data_dir):
    """Test that batch processing actually produces correspondence and tracking results"""
    test_dir = test_data_dir
    yaml_file = test_dir / "parameters_Run1.yaml"
    
    # Test specific frame
    start_frame = 10000
    end_frame = 10004
    
    # Clear any existing results
    res_dir = test_dir / "res"
    if res_dir.exists():
        import shutil
        shutil.rmtree(res_dir)
    
    # Run batch processing
    pyptv_batch.main(yaml_file, start_frame, end_frame)
    
    # Check that result files were created
    assert res_dir.exists(), "Results directory should be created"
    
    # Check for correspondence files
    corres_file = res_dir / f"rt_is.{start_frame}"
    assert corres_file.exists(), f"Correspondence file {corres_file} should exist"
    
    # Check that correspondence file has content (more than just "0\n")
    content = corres_file.read_text()
    lines = content.strip().split('\n')
    assert len(lines) > 1, "Correspondence file should have more than just the count line"
    
    # First line should be the number of points
    num_points = int(lines[0])
    assert num_points > 0, f"Should have detected correspondences, got {num_points}"
    assert num_points == len(lines) - 1, "Number of points should match number of data lines"
    
    print(f"Successfully detected {num_points} correspondences in frame {start_frame}")


def test_pyptv_batch_tracking_results(test_data_dir):
    """Test that batch processing with multiple frames produces tracking results and validates output."""
    test_dir = test_data_dir
    yaml_file = test_dir / "parameters_Run1.yaml"
    start_frame = 10000
    end_frame = 10004
    res_dir = test_dir / "res"
    if res_dir.exists():
        import shutil
        shutil.rmtree(res_dir)
    pyptv_batch.main(yaml_file, start_frame, end_frame)
    for frame in [start_frame, end_frame]:
        corres_file = res_dir / f"rt_is.{frame}"
        assert corres_file.exists(), f"Correspondence file for frame {frame} should exist"
        content = corres_file.read_text()
        lines = content.strip().split('\n')
        num_points = int(lines[0])
        assert num_points > 0, f"Frame {frame} should have correspondences, got {num_points}"
        assert num_points == len(lines) - 1, f"Number of points should match number of data lines in {corres_file}"
    print(f"Successfully processed frames {start_frame} to {end_frame} with tracking")


def test_pyptv_batch_tracking_mode_only(test_data_dir):
    """Test batch processing with mode='tracking' only, with debug output"""
    test_dir = test_data_dir
    yaml_file = test_dir / "parameters_Run1.yaml"
    start_frame = 10000
    end_frame = 10004
    res_dir = test_dir / "res"
    if res_dir.exists():
        import shutil
        shutil.rmtree(res_dir)
    print(f"Running tracking mode with YAML: {yaml_file}")
    print(f"Frame range: {start_frame} to {end_frame}")
    pyptv_batch.main(yaml_file, start_frame, end_frame, mode="sequence")
    try:
        pyptv_batch.main(yaml_file, start_frame, end_frame, mode="tracking")
    except Exception as e:
        print(f"Tracking mode batch processing failed: {str(e)}")
        pytest.fail(f"Tracking mode batch processing failed: {str(e)}")
    # Check for tracking output files (these depend on the tracker configuration)
    # At minimum, we should have some output indicating tracking was attempted
    assert res_dir.exists(), "Results directory should be created in tracking mode"
    print(f"Tracking mode test completed for frames {start_frame} to {end_frame}")
    # Print correspondence file contents for debug
    for frame in range(start_frame, end_frame + 1):
        corres_file = res_dir / f"rt_is.{frame}"
        if corres_file.exists():
            print(f"Contents of {corres_file}:")
            print(corres_file.read_text())
        else:
            print(f"Correspondence file {corres_file} does not exist.")


def test_pyptv_batch_tracking_mode_only_with_temp_yaml(test_data_dir):
    """Test tracking mode only, using a temporary copy of the original YAML file. Print tracking parameters before running tracking."""
    import tempfile
    import shutil
    import yaml
    test_dir = test_data_dir
    orig_yaml = test_dir / "parameters_Run1.yaml"
    start_frame = 10000
    end_frame = 10004
    res_dir = test_dir / "res"
    if res_dir.exists():
        shutil.rmtree(res_dir)
    # Copy original YAML to temp file
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.yaml', dir=test_dir) as tmp:
        temp_yaml = tmp.name
        with open(orig_yaml, 'r') as orig_f:
            orig_content = yaml.safe_load(orig_f)
        yaml.safe_dump(orig_content, tmp)
    print(f"Running tracking mode with temp YAML: {temp_yaml}")
    print(f"Frame range: {start_frame} to {end_frame}")
    pyptv_batch.main(temp_yaml, start_frame, end_frame, mode="sequence")
    # Extract and print tracking parameters
    with open(temp_yaml, 'r') as f:
        params = yaml.safe_load(f)
    track_params = params.get('track', {})
    print("Tracking parameters:")
    for k, v in track_params.items():
        print(f"  {k}: {v}")
    try:
        pyptv_batch.main(temp_yaml, start_frame, end_frame, mode="tracking")
    except Exception as e:
        print(f"Tracking mode batch processing failed: {str(e)}")
        pytest.fail(f"Tracking mode batch processing failed: {str(e)}")
    assert res_dir.exists(), "Results directory should be created in tracking mode"
    print(f"Tracking mode test completed for frames {start_frame} to {end_frame}")
    for frame in range(start_frame, end_frame+1):
        corres_file = res_dir / f"rt_is.{frame}"
        if corres_file.exists():
            print(f"Contents of {corres_file}:")
            print(corres_file.read_text())
        else:
            print(f"Correspondence file {corres_file} does not exist.")


def test_pyptv_batch_tracking_mode_only_with_temp_yaml_collect_results(test_data_dir):
    """Test tracking mode only, collect tracking parameters and average output in a pandas DataFrame, parsing 'Average over sequence' output from file. Print output for debugging if subprocess fails."""
    import tempfile
    import shutil
    import yaml
    import re
    import subprocess
    test_dir = test_data_dir
    orig_yaml = test_dir / "parameters_Run1.yaml"
    start_frame = 10000
    end_frame = 10004
    res_dir = test_dir / "res"
    if res_dir.exists():
        shutil.rmtree(res_dir)
    # Copy original YAML to temp file
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.yaml', dir=test_dir) as tmp:
        temp_yaml = tmp.name
        with open(orig_yaml, 'r') as orig_f:
            orig_content = yaml.safe_load(orig_f)
        yaml.safe_dump(orig_content, tmp)
    # Extract tracking parameters
    with open(temp_yaml, 'r') as f:
        params = yaml.safe_load(f)
    track_params = params.get('track', {})
    # Run sequence mode (no need to capture output)
    pyptv_batch.main(temp_yaml, start_frame, end_frame, mode="sequence")
    # Run tracking mode and capture output to file, set cwd to test_dir
    with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.txt', dir=test_dir) as out_file:
        out_path = out_file.name
        cmd = [sys.executable, '-m', 'pyptv.pyptv_batch', os.path.basename(temp_yaml), str(start_frame), str(end_frame), '--mode', 'tracking']
        try:
            subprocess.run(cmd, stdout=out_file, stderr=subprocess.STDOUT, check=True, cwd=test_dir)
        except subprocess.CalledProcessError:
            out_file.flush()
            with open(out_path, 'r') as f:
                print("\n--- Subprocess output ---")
                print(f.read())
            raise
    # Parse 'Average over sequence' line from file
    avg_particles = avg_links = avg_lost = None
    with open(out_path, 'r') as f:
        for line in f:
            m = re.search(r"Average over sequence, particles:\s*([\d\.-]+), links:\s*([\d\.-]+), lost:\s*([\d\.-]+)", line)
            if m:
                avg_particles = float(m.group(1))
                avg_links = float(m.group(2))
                avg_lost = float(m.group(3))
                break
    # Create DataFrame to collect results
    results = []
    # Store original run
    row = {**track_params, 'avg_particles': avg_particles, 'avg_links': avg_links, 'avg_lost': avg_lost, 'param_changed': None, 'change': 0.0}
    results.append(row)

    # Loop: for each numeric track_param, perturb by +10% and rerun tracking
    for param, value in track_params.items():
        if isinstance(value, (int, float)):
            # Create new temp YAML with perturbed parameter
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.yaml', dir=test_dir) as tmp2:
                temp_yaml2 = tmp2.name
                with open(orig_yaml, 'r') as orig_f:
                    orig_content2 = yaml.safe_load(orig_f)
                # Update the parameter by +10%
                new_val = value * 1.1
                orig_content2['track'][param] = type(value)(new_val)
                yaml.safe_dump(orig_content2, tmp2)
            # Run sequence mode (to prep files)
            pyptv_batch.main(temp_yaml2, start_frame, end_frame, mode="sequence")
            # Run tracking mode and capture output
            with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.txt', dir=test_dir) as out_file2:
                out_path2 = out_file2.name
                cmd2 = [sys.executable, '-m', 'pyptv.pyptv_batch', os.path.basename(temp_yaml2), str(start_frame), str(end_frame), '--mode', 'tracking']
                try:
                    subprocess.run(cmd2, stdout=out_file2, stderr=subprocess.STDOUT, check=True, cwd=test_dir)
                except subprocess.CalledProcessError:
                    out_file2.flush()
                    with open(out_path2, 'r') as f:
                        print(f"\n--- Subprocess output for {param} +10% ---")
                        print(f.read())
                    continue  # Skip this run if it failed
            # Parse output
            avg_particles2 = avg_links2 = avg_lost2 = None
            with open(out_path2, 'r') as f:
                for line in f:
                    m = re.search(r"Average over sequence, particles:\s*([\d\.-]+), links:\s*([\d\.-]+), lost:\s*([\d\.-]+)", line)
                    if m:
                        avg_particles2 = float(m.group(1))
                        avg_links2 = float(m.group(2))
                        avg_lost2 = float(m.group(3))
                        break
            # Store result
            perturbed_params = dict(track_params)
            perturbed_params[param] = type(value)(new_val)
            row2 = {**perturbed_params, 'avg_particles': avg_particles2, 'avg_links': avg_links2, 'avg_lost': avg_lost2, 'param_changed': param, 'change': 0.1}
            results.append(row2)

    df = pd.DataFrame(results)
    print("\nTracking run summary (including perturbations):")
    print(df)
    df.to_csv(test_dir / "tracking_run_summary.csv", index=False)

    # Find best row: least avg_lost, then most avg_links
    best = df.sort_values(['avg_lost', 'avg_links'], ascending=[True, False]).iloc[0]
    print("\nBest tracking result (least lost, most links):")
    print(best)


def optimize_tracking_parameters(test_data_dir):
    """Optimize tracking parameters using scipy.optimize to minimize lost links and maximize avg_links."""
    import tempfile
    import shutil
    import yaml
    import re
    import subprocess
    import numpy as np
    from scipy.optimize import minimize

    test_dir = test_data_dir
    orig_yaml = test_dir / "parameters_Run1.yaml"
    start_frame = 10000
    end_frame = 10004  # Use only 2 frames for speed
    res_dir = test_dir / "res"
    if res_dir.exists():
        shutil.rmtree(res_dir)
    # Load original tracking parameters
    with open(orig_yaml, 'r') as f:
        params = yaml.safe_load(f)
    track_params = params.get('track', {})
    # Only optimize numeric parameters
    param_names = [k for k, v in track_params.items() if isinstance(v, (int, float))]
    orig_values = np.array([track_params[k] for k in param_names], dtype=float)

    def loss_fn(x):
        # Create temp YAML file with updated parameters
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.yaml', dir=test_dir) as tmp:
            temp_yaml = tmp.name
            with open(orig_yaml, 'r') as orig_f:
                orig_content = yaml.safe_load(orig_f)
            for i, k in enumerate(param_names):
                orig_content['track'][k] = float(x[i])
            yaml.safe_dump(orig_content, tmp)
        # Run sequence mode (to prep files)
        pyptv_batch.main(temp_yaml, start_frame, end_frame, mode="sequence")
        # Run tracking mode and capture output
        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.txt', dir=test_dir) as out_file:
            out_path = out_file.name
            cmd = [sys.executable, '-m', 'pyptv.pyptv_batch', os.path.basename(temp_yaml), str(start_frame), str(end_frame), '--mode', 'tracking']
            try:
                subprocess.run(cmd, stdout=out_file, stderr=subprocess.STDOUT, check=True, cwd=test_dir)
            except subprocess.CalledProcessError:
                out_file.flush()
                with open(out_path, 'r') as f:
                    print("\n--- Subprocess output (optimization step) ---")
                    print(f.read())
                return 1e6  # Large penalty for failed run
        # Parse output
        avg_lost = avg_links = None
        with open(out_path, 'r') as f:
            for line in f:
                m = re.search(r"Average over sequence, particles:\s*([\d\.-]+), links:\s*([\d\.-]+), lost:\s*([\d\.-]+)", line)
                if m:
                    avg_links = float(m.group(2))
                    avg_lost = float(m.group(3))
                    break
        if avg_lost is None or avg_links is None:
            return 1e5  # Penalty if output not found
        # Loss: minimize lost, maximize links (weighted sum)
        return avg_lost - 0.1 * avg_links

    # Run optimization with multiple random restarts to escape local minima
    best_result = None
    n_restarts = 2  # Fewer restarts for speed
    for i in range(n_restarts):
        # Randomize initial values within ±20% of original
        x0 = orig_values * (0.8 + 0.4 * np.random.rand(*orig_values.shape))
        result = minimize(loss_fn, x0, method='Powell', options={'maxiter': 30, 'disp': True})
        print(f"\nRestart {i+1}: loss={result.fun}, params={result.x}")
        if best_result is None or result.fun < best_result.fun:
            best_result = result
    best_values = best_result.x
    best_loss = best_result.fun
    print("\nOptimization result (best of restarts):")
    print(f"Best parameters: {dict(zip(param_names, best_values))}")
    print(f"Best loss: {best_loss}")
    print(f"Original values: {dict(zip(param_names, orig_values))}")
    assert best_result.success, f"Optimization failed: {best_result.message}"


# def test_optimize_tracking_parameters(test_data_dir):
#     """Test optimization of tracking parameters using gradient descent."""
#     optimize_tracking_parameters(test_data_dir)


if __name__ == "__main__":
    pytest.main([__file__])