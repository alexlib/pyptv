#!/usr/bin/env python3
"""
Test script for the improved ParameterManager functionality
"""

from pyptv.parameter_manager import ParameterManager

def test_parameter_manager():
    print("=== Testing ParameterManager improvements ===")
    
    # Test the new functionality
    pm = ParameterManager()

    # Test with empty parameters
    print('\n1. Testing missing parameter handling')
    result = pm.get_parameter('masking')
    print(f'   masking (not exists): {result}')

    result = pm.get_parameter('masking', default={'mask_flag': False})
    print(f'   masking (with default): {result}')

    # Test parameter value extraction
    result = pm.get_parameter_value('nonexistent_group', 'some_key', default='default_value')
    print(f'   nonexistent parameter: {result}')

    # Test has_parameter
    print(f'   has masking: {pm.has_parameter("masking")}')

    print('\n2. Testing ensure_default_parameters')
    pm.ensure_default_parameters()
    print(f'   masking after defaults: {pm.get_parameter("masking")}')
    print(f'   has masking now: {pm.has_parameter("masking")}')
    
    # Test parameter value extraction after defaults
    print('\n3. Testing parameter value extraction after defaults')
    mask_flag = pm.get_parameter_value('masking', 'mask_flag')
    print(f'   masking.mask_flag: {mask_flag}')
    
    nonexistent = pm.get_parameter_value('masking', 'nonexistent_key', default='N/A')
    print(f'   masking.nonexistent_key: {nonexistent}')
    
    print('\n=== Test completed successfully! ===')

if __name__ == '__main__':
    test_parameter_manager()
