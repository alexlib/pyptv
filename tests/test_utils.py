"""
Test utilities for PyPTV tests to ensure proper cleanup and isolation.
"""

import os
from contextlib import contextmanager


@contextmanager
def temporary_working_directory(path):
    """
    Context manager to temporarily change working directory and always restore it.
    
    This ensures tests don't affect each other by leaving the working directory
    in an unexpected state.
    
    Args:
        path: The path to change to temporarily
        
    Yields:
        None
    """
    original_dir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(original_dir)


@contextmanager 
def preserve_working_directory():
    """
    Context manager to preserve the current working directory.
    
    Use this when you want to ensure the working directory is restored
    even if the code inside changes it.
    
    Yields:
        None
    """
    original_dir = os.getcwd()
    try:
        yield
    finally:
        os.chdir(original_dir)
