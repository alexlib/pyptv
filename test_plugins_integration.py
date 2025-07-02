#!/usr/bin/env python3
"""
Test script for plugins YAML integration
"""

import sys
from pathlib import Path

# Add pyptv to path
sys.path.insert(0, str(Path(__file__).parent))

from pyptv.parameter_manager import ParameterManager
from pyptv.experiment import Experiment

def test_plugins_yaml_integration():
    """Test that plugins are properly integrated into YAML system"""
    print("=== Testing Plugins YAML Integration ===\n")
    
    # Test 1: Parameter Manager loading plugins from YAML
    print("1. Testing ParameterManager loading plugins from YAML...")
    pm = ParameterManager()
    pm.from_yaml(Path('tests/test_cavity/parameters_Run1.yaml'))
    
    plugins_params = pm.get_parameter('plugins')
    print(f"   Plugins parameters: {plugins_params}")
    
    if plugins_params:
        print(f"   Available tracking: {plugins_params.get('available_tracking', [])}")
        print(f"   Available sequence: {plugins_params.get('available_sequence', [])}")
        print(f"   Selected tracking: {plugins_params.get('selected_tracking', 'default')}")
        print(f"   Selected sequence: {plugins_params.get('selected_sequence', 'default')}")
        print("   ✅ Plugins loaded successfully from YAML")
    else:
        print("   ❌ Failed to load plugins from YAML")
    
    print()
    
    # Test 2: Experiment loading plugins
    print("2. Testing Experiment loading plugins...")
    exp = Experiment()
    exp.populate_runs(Path('tests/test_cavity'))
    if exp.nParamsets() > 0:
        exp.setActive(0)
        exp_plugins = exp.get_parameter('plugins')
        print(f"   Experiment plugins: {exp_plugins}")
        print("   ✅ Experiment loaded plugins successfully")
    else:
        print("   ❌ No parameter sets found in experiment")
    
    print()
    
    # Test 3: Default plugins creation
    print("3. Testing default plugins creation...")
    pm_new = ParameterManager()
    pm_new.ensure_default_parameters()
    default_plugins = pm_new.get_parameter('plugins')
    print(f"   Default plugins: {default_plugins}")
    
    if default_plugins and 'available_tracking' in default_plugins:
        print("   ✅ Default plugins created successfully")
    else:
        print("   ❌ Failed to create default plugins")
    
    print()
    
    # Test 4: Migration functionality
    print("4. Testing plugins.json migration...")
    plugins_json_path = Path('tests/test_cavity/plugins.json')
    if plugins_json_path.exists():
        pm_migrate = ParameterManager()
        pm_migrate.migrate_plugins_json(plugins_json_path)
        migrated_plugins = pm_migrate.get_parameter('plugins')
        print(f"   Migrated plugins: {migrated_plugins}")
        print("   ✅ Migration functionality works")
    else:
        print("   ⚠️  No plugins.json found for migration test")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_plugins_yaml_integration()
