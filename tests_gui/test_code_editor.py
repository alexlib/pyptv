import tempfile
import shutil
from pathlib import Path
import pytest
from pyptv.experiment import Experiment
from pyptv.code_editor import oriEditor, addparEditor


def make_dummy_experiment(tmp_path):
    # Create dummy YAML and files for experiment
    yaml_path = tmp_path / "parameters.yaml"
    img_ori = []
    for i in range(2):
        ori_file = tmp_path / f"cam{i+1}.ori"
        addpar_file = tmp_path / f"cam{i+1}.addpar"
        ori_file.write_text(f"ori file {i+1}")
        addpar_file.write_text(f"addpar file {i+1}")
        img_ori.append(str(ori_file))
    params = {
        'num_cams': 2,
        "ptv": {"n_img": 2},
        "cal_ori": {"img_ori": img_ori}
    }
    import yaml
    yaml_path.write_text(yaml.safe_dump(params))
    exp = Experiment()
    exp.pm.from_yaml(yaml_path)
    return exp, img_ori


def test_ori_editor(tmp_path):
    exp, img_ori = make_dummy_experiment(tmp_path)
    editor = oriEditor(exp)
    assert editor.n_img == 2
    assert len(editor.oriEditors) == 2
    for i, code_editor in enumerate(editor.oriEditors):
        assert code_editor.file_Path == Path(img_ori[i])
        assert code_editor._Code == f"ori file {i+1}"


def test_addpar_editor(tmp_path):
    exp, img_ori = make_dummy_experiment(tmp_path)
    editor = addparEditor(exp)
    assert editor.n_img == 2
    assert len(editor.addparEditors) == 2
    for i, code_editor in enumerate(editor.addparEditors):
        expected_path = Path(img_ori[i].replace("ori", "addpar"))
        assert code_editor.file_Path == expected_path
        assert code_editor._Code == f"addpar file {i+1}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
    # Run the tests directly if this script is executed