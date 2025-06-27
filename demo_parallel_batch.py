#!/usr/bin/env python3
"""
Demonstration script for the improved pyptv_batch_parallel.py functionality.

This script shows how to use the improved parallel batch processing with
proper logging, error handling, and CPU optimization.
"""

import sys
import tempfile
import shutil
import multiprocessing
from pathlib import Path
import logging

# Import our improved pyptv_batch_parallel components
from pyptv.pyptv_batch_parallel import (
    main, 
    chunk_ranges,
    validate_experiment_directory, 
    ProcessingError,
    AttrDict,
    logger
)

def create_test_experiment_directory():
    """Create a temporary test experiment directory with required structure."""
    temp_dir = tempfile.mkdtemp()
    exp_path = Path(temp_dir) / "test_experiment"
    exp_path.mkdir()
    
    # Create required directories
    for dirname in ["parameters", "img", "cal", "res"]:
        (exp_path / dirname).mkdir()
    
    # Create ptv.par file with camera count
    ptv_par = exp_path / "parameters" / "ptv.par"
    ptv_par.write_text("4\n")  # 4 cameras for test
    
    logger.info(f"Created test experiment directory: {exp_path}")
    return exp_path, temp_dir

def demonstrate_chunk_ranges():
    """Demonstrate frame range chunking functionality."""
    logger.info("=== Demonstrating Frame Range Chunking ===")
    
    test_cases = [
        (1000, 1019, 4),   # 20 frames, 4 processes
        (1000, 1010, 3),   # 11 frames, 3 processes  
        (1000, 1005, 8),   # 6 frames, 8 processes (more processes than frames)
        (1000, 1000, 2),   # 1 frame, 2 processes
    ]
    
    for first, last, n_processes in test_cases:
        total_frames = last - first + 1
        logger.info(f"Chunking {total_frames} frames ({first}-{last}) into {n_processes} processes:")
        
        try:
            ranges = chunk_ranges(first, last, n_processes)
            for i, (chunk_first, chunk_last) in enumerate(ranges):
                chunk_size = chunk_last - chunk_first + 1
                logger.info(f"  Process {i+1}: frames {chunk_first}-{chunk_last} ({chunk_size} frames)")
        except Exception as e:
            logger.error(f"  Error: {e}")
        
        logger.info("")

def demonstrate_cpu_optimization():
    """Demonstrate CPU count detection and optimization recommendations."""
    logger.info("=== CPU Optimization Demonstration ===")
    
    cpu_count = multiprocessing.cpu_count()
    logger.info(f"Available CPU cores: {cpu_count}")
    
    # Demonstrate different process count scenarios
    scenarios = [
        ("Conservative (50% of cores)", max(1, cpu_count // 2)),
        ("Moderate (75% of cores)", max(1, int(cpu_count * 0.75))),
        ("Aggressive (100% of cores)", cpu_count),
        ("Over-subscription (150% of cores)", int(cpu_count * 1.5)),
    ]
    
    for description, n_processes in scenarios:
        logger.info(f"{description}: {n_processes} processes")
        if n_processes > cpu_count:
            logger.warning(f"  ⚠️  Over-subscription may reduce performance")
        elif n_processes == cpu_count:
            logger.info(f"  ✓ Optimal for CPU-bound tasks")
        else:
            logger.info(f"  ✓ Conservative, leaves resources for system")
    
    logger.info("")

def demonstrate_error_handling():
    """Demonstrate error handling in parallel processing."""
    logger.info("=== Error Handling Demonstration ===")
    
    try:
        # Test invalid frame range
        chunk_ranges(2000, 1000, 4)
    except ValueError as e:
        logger.info(f"✓ Caught invalid frame range: {e}")
    
    try:
        # Test invalid process count
        chunk_ranges(1000, 2000, 0)
    except ValueError as e:
        logger.info(f"✓ Caught invalid process count: {e}")
    
    # Test directory validation
    try:
        nonexistent_path = Path("/nonexistent/directory")
        validate_experiment_directory(nonexistent_path)
    except ProcessingError as e:
        logger.info(f"✓ Caught directory validation error: {e}")
    
    logger.info("")

def simulate_parallel_processing():
    """Simulate the parallel processing workflow."""
    logger.info("=== Simulating Parallel Processing Workflow ===")
    
    exp_path, temp_dir = create_test_experiment_directory()
    
    try:
        logger.info("Starting simulated parallel batch processing...")
        
        # Validate directory (should succeed)
        validate_experiment_directory(exp_path)
        logger.info("✓ Directory validation completed")
        
        # Demonstrate chunking for different scenarios
        test_scenarios = [
            (1000, 1019, 4, "Optimal chunking: 20 frames, 4 processes"),
            (1000, 1050, 8, "Large dataset: 51 frames, 8 processes"),
            (1000, 1005, 2, "Small dataset: 6 frames, 2 processes"),
        ]
        
        for seq_first, seq_last, n_processes, description in test_scenarios:
            logger.info(f"\n{description}")
            total_frames = seq_last - seq_first + 1
            
            ranges = chunk_ranges(seq_first, seq_last, n_processes)
            logger.info(f"  Total frames: {total_frames}")
            logger.info(f"  Processes: {n_processes}")
            logger.info(f"  Chunks: {len(ranges)}")
            
            for i, (chunk_first, chunk_last) in enumerate(ranges):
                chunk_size = chunk_last - chunk_first + 1
                logger.info(f"    Process {i+1}: {chunk_first}-{chunk_last} ({chunk_size} frames)")
        
        logger.info("\n✓ Simulated processing setup completed")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
    finally:
        shutil.rmtree(temp_dir)

def demonstrate_performance_considerations():
    """Demonstrate performance considerations for parallel processing."""
    logger.info("=== Performance Considerations ===")
    
    cpu_count = multiprocessing.cpu_count()
    
    logger.info("Guidelines for choosing number of processes:")
    logger.info("1. CPU-bound tasks (like image processing):")
    logger.info(f"   - Optimal: {cpu_count} processes (one per core)")
    logger.info(f"   - Conservative: {max(1, cpu_count // 2)} processes (50% of cores)")
    
    logger.info("\n2. I/O-bound tasks (reading many files):")
    logger.info(f"   - Can use more: {cpu_count * 2} processes")
    logger.info("   - Limited by storage speed, not CPU")
    
    logger.info("\n3. Memory considerations:")
    logger.info("   - Each process loads full experiment data")
    logger.info("   - Monitor memory usage with many processes")
    logger.info("   - Reduce processes if memory becomes limiting factor")
    
    logger.info("\n4. Frame range considerations:")
    frame_scenarios = [
        (100, "Very small dataset - consider sequential processing"),
        (1000, "Small dataset - 2-4 processes optimal"),
        (10000, "Medium dataset - 4-8 processes optimal"),
        (100000, "Large dataset - 8+ processes beneficial"),
    ]
    
    for frames, recommendation in frame_scenarios:
        logger.info(f"   - {frames} frames: {recommendation}")
    
    logger.info("")

def main_demo():
    """Run all demonstrations."""
    logger.info("PyPTV Parallel Batch Processing Demonstration")
    logger.info("=" * 60)
    
    # Run all demonstrations
    demonstrate_chunk_ranges()
    demonstrate_cpu_optimization()
    demonstrate_error_handling()
    simulate_parallel_processing()
    demonstrate_performance_considerations()
    
    logger.info("=" * 60)
    logger.info("Demonstration completed successfully!")
    
    # Show environment information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"CPU cores available: {multiprocessing.cpu_count()}")
    logger.info(f"Running from: {sys.executable}")

if __name__ == "__main__":
    # Configure logging to show all messages
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        main_demo()
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        sys.exit(1)
