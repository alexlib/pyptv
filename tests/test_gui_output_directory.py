from types import SimpleNamespace

import pytest

from pyptv.pyptv_gui import MainGUI


class TestEnsureResDirectoryReady:
    def test_creates_missing_res_directory(self, tmp_path, capsys):
        dummy_gui = SimpleNamespace(exp_path=tmp_path)

        result = MainGUI.ensure_res_directory_ready(dummy_gui)
        output = capsys.readouterr().out

        assert result == tmp_path / "res"
        assert result.is_dir()
        assert not (result / ".pyptv_write_probe").exists()
        assert "Creating output directory" in output
        assert "is writable" in output
        assert "will overwrite files there" not in output

    def test_warns_when_res_directory_exists(self, tmp_path, capsys):
        res_dir = tmp_path / "res"
        res_dir.mkdir()
        dummy_gui = SimpleNamespace(exp_path=tmp_path)

        result = MainGUI.ensure_res_directory_ready(dummy_gui)
        output = capsys.readouterr().out

        assert result == res_dir
        assert "will overwrite files there" in output
        assert "is writable" in output

    def test_raises_when_res_directory_is_not_writable(self, tmp_path):
        dummy_gui = SimpleNamespace(exp_path=tmp_path)

        with pytest.raises(PermissionError, match="Cannot write output file"):
            with pytest.MonkeyPatch.context() as monkeypatch:
                monkeypatch.setattr(
                    "builtins.open",
                    lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError("denied")),
                )
                MainGUI.ensure_res_directory_ready(dummy_gui)