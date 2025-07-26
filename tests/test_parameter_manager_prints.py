import yaml
from pyptv.parameter_manager import ParameterManager


def test_print_cavity_yaml():
    pm = ParameterManager()
    pm.from_directory('tests/test_cavity/parameters')
    print('\n--- YAML for test_cavity ---')
    print(yaml.dump(pm.parameters, sort_keys=False, default_flow_style=False))


def test_print_splitter_yaml():
    pm = ParameterManager()
    pm.from_directory('tests/test_splitter/parameters')
    print('\n--- YAML for test_splitter ---')
    print(yaml.dump(pm.parameters, sort_keys=False, default_flow_style=False))
