import tempfile
import shutil
import os
import yaml
from pathlib import Path
from pyptv.parameter_manager import ParameterManager

def create_dummy_par_dir(tmpdir):
    tmp_dir = Path(tmpdir)
    tmp_dir.mkdir(exist_ok=True)
    par_dir = tmp_dir / 'parameters'
    par_dir.mkdir(exist_ok=True)
    n_img = 2
    # ptv.par
    ptv_lines = [
        f"{n_img}",
        "img1.tif", "cal1.dat",
        "img2.tif", "cal2.dat",
        "1", "0", "1", "2048", "2048", "0.01", "0.01", "0", "1.33", "1.0", "0.0", "0.0"
    ]
    (par_dir / 'ptv.par').write_text('\n'.join(ptv_lines) + '\n')
    # cal_ori.par
    cal_ori_lines = [
        "fixpoints.dat",
        "cal1.dat", "ori1.dat",
        "cal2.dat", "ori2.dat",
        "1", "0", "0"
    ]
    (par_dir / 'cal_ori.par').write_text('\n'.join(cal_ori_lines) + '\n')
    # sequence.par
    seq_lines = ["basename1", "basename2", "1", "100"]
    (par_dir / 'sequence.par').write_text('\n'.join(seq_lines) + '\n')
    # criteria.par
    crit_lines = ["1", "2", "3", "4", "5", "6", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6"]
    (par_dir / 'criteria.par').write_text('\n'.join(crit_lines) + '\n')
    # track.par
    track_lines = ["-1.0", "1.0", "-1.0", "1.0", "-1.0", "1.0", "45.0", "0.5", "1"]
    (par_dir / 'track.par').write_text('\n'.join(track_lines) + '\n')
    # detect_plate.par
    detect_plate_lines = [str(i) for i in range(1, 14)]
    (par_dir / 'detect_plate.par').write_text('\n'.join(detect_plate_lines) + '\n')
    # man_ori.par
    man_ori_lines = ["0", "0", "0", "0", "0", "0", "0", "0"]
    (par_dir / 'man_ori.par').write_text('\n'.join(man_ori_lines) + '\n')
    # plugins
    plugins_dir = tmp_dir / 'plugins'
    plugins_dir.mkdir(exist_ok=True)
    (plugins_dir / 'my_sequence_.py').write_text('# dummy sequence plugin')
    (plugins_dir / 'my_tracker_.py').write_text('# dummy tracking plugin')
    return par_dir

def test_parameter_manager_yaml_plugins():
    with tempfile.TemporaryDirectory() as tmpdir:
        par_dir = create_dummy_par_dir(tmpdir)
        yaml_path = par_dir / 'params.yaml'
        pm = ParameterManager()
        pm.from_directory(par_dir)
        pm.scan_plugins(par_dir / 'plugins')
        pm.to_yaml(yaml_path)
        # Print YAML
        with open(yaml_path) as f:
            ydata = yaml.safe_load(f)
            print('\n--- YAML OUTPUT ---')
            print(yaml.dump(ydata, default_flow_style=False, sort_keys=False))
        # Check all major sections
        assert 'ptv' in ydata
        assert 'cal_ori' in ydata
        assert 'track' in ydata
        assert 'criteria' in ydata
        assert 'detect_plate' in ydata
        assert 'man_ori' in ydata
        # Check splitter and cal_splitter
        assert 'splitter' in ydata['ptv']
        assert 'cal_splitter' in ydata['cal_ori']
        # Check plugins section
        assert 'plugins' in ydata
        plugins = ydata['plugins']
        
        assert 'selected_sequence' in plugins
        assert 'selected_tracking' in plugins
        # Check that dummy plugins are listed
        assert 'my_sequence_' in plugins['available_sequence']
        assert 'my_tracker_' in plugins['available_tracking']
        # Check default selection
        assert plugins['selected_sequence'] == 'default'
        assert plugins['selected_tracking'] == 'default'

if __name__ == '__main__':
    test_parameter_manager_yaml_plugins()
    print('Test completed.')
