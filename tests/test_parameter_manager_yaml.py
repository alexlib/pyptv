#!/usr/bin/env python3
"""
Test script for the YAML-centric ParameterManager functionality
"""

import pytest
from pathlib import Path
import tempfile
import os
from pyptv.parameter_manager import ParameterManager, create_parameter_template


def test_parameter_manager_creation():
    """Test ParameterManager creation"""
    pm = ParameterManager()
    assert pm is not None
    assert pm.parameters == {}
    assert pm.yaml_path is None


def test_parameter_template_creation():
    """Test creating parameter template"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yaml_file = Path(temp_dir) / "parameters_Test.yaml"
        pm = create_parameter_template(yaml_file, n_cam=3)
        
        assert yaml_file.exists()
        assert pm.get_n_cam() == 3
        assert pm.get_parameter('ptv') is not None
        assert len(pm.get_parameter('ptv.img_name')) == 3


def test_parameter_access():
    """Test parameter access methods"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yaml_file = Path(temp_dir) / "parameters_Test.yaml"
        pm = create_parameter_template(yaml_file)
        
        # Test get_parameter
        ptv_params = pm.get_parameter('ptv')
        assert ptv_params is not None
        assert isinstance(ptv_params, dict)
        
        # Test nested parameter access
        imx = pm.get_parameter('ptv.imx')
        assert imx == 1024  # Default value
        
        # Test default values
        missing = pm.get_parameter('nonexistent', default='default_value')
        assert missing == 'default_value'


def test_parameter_modification():
    """Test parameter modification"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yaml_file = Path(temp_dir) / "parameters_Test.yaml"
        pm = create_parameter_template(yaml_file)
        
        # Test set_parameter
        pm.set_parameter('ptv.imx', 2048)
        assert pm.get_parameter('ptv.imx') == 2048
        
        # Test nested parameter setting
        pm.set_parameter('new_group.new_param', 'test_value')
        assert pm.get_parameter('new_group.new_param') == 'test_value'


def test_yaml_save_load():
    """Test YAML save and load functionality"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yaml_file = Path(temp_dir) / "parameters_Test.yaml"
        
        # Create and modify parameters
        pm1 = create_parameter_template(yaml_file)
        pm1.set_parameter('ptv.imx', 2048)
        pm1.set_parameter('test_param', 'test_value')
        pm1.save_yaml()
        
        # Load parameters in new instance
        pm2 = ParameterManager(yaml_file)
        assert pm2.get_parameter('ptv.imx') == 2048
        assert pm2.get_parameter('test_param') == 'test_value'


def test_path_resolution():
    """Test path resolution functionality"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yaml_file = Path(temp_dir) / "parameters_Test.yaml"
        pm = create_parameter_template(yaml_file)
        
        # Test resolve_path
        relative_path = "img/cam1.tif"
        absolute_path = pm.resolve_path(relative_path)
        expected_path = Path(temp_dir) / relative_path
        assert absolute_path == expected_path


def test_working_directory():
    """Test working directory functionality"""
    original_cwd = Path.cwd()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        yaml_file = Path(temp_dir) / "parameters_Test.yaml"
        pm = create_parameter_template(yaml_file)
        
        # Working directory should be set to YAML file location
        assert pm.get_working_directory() == Path(temp_dir)
        assert Path.cwd() == Path(temp_dir)
    
    # Restore original working directory
    os.chdir(original_cwd)


if __name__ == "__main__":
    test_parameter_manager_creation()
    test_parameter_template_creation()
    test_parameter_access() 
    test_parameter_modification()
    test_yaml_save_load()
    test_path_resolution()
    test_working_directory()
    print("All ParameterManager tests passed!")
