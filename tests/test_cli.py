from pyptv import cli


def test_cli_template():
    assert cli.cli() == "CLI template"
