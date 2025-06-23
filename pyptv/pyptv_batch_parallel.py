"""
PyPTV_BATCH_PARALLEL: Parallel batch processing for 3D-PTV

This script runs the sequence (detection/correspondence) step in parallel
by splitting the frame range into chunks, each processed by a separate process.

Usage:
    python pyptv_batch_parallel.py <experiment_path> <seq_first> <seq_last> <n_processes>

Arguments:
    <experiment_path>   Path to the experiment folder (e.g. experiments/exp1)
    <seq_first>         First frame number in the sequence (e.g. 10001)
    <seq_last>          Last frame number in the sequence (e.g. 11001)
    <n_processes>       Number of parallel processes to use (e.g. 4)

Example:
    python pyptv_batch_parallel.py experiments/exp1 10001 11001 4

This will split the frame range 10001–11001 into 4 chunks and process each chunk in parallel.
Each process will run detection and correspondence for its assigned chunk of frames.

Notes:
- Choose <n_processes> based on the number of CPU cores available on your machine.
- Results are written to the 'res' folder inside the experiment directory.
- Tracking is not parallelized in this script; only the sequence step is parallel.

"""

import sys
import os
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

from pyptv.ptv import py_start_proc_c, py_sequence_loop

def run_sequence_chunk(exp_path, seq_first, seq_last):
    """Run sequence for a chunk of frames in a separate process."""
    exp_path = Path(exp_path).resolve()
    os.chdir(exp_path)
    with open("parameters/ptv.par", "r") as f:
        n_cams = int(f.readline())
    cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(n_cams=n_cams)
    spar.set_first(seq_first)
    spar.set_last(seq_last)
    exp = {
        "cpar": cpar,
        "spar": spar,
        "vpar": vpar,
        "track_par": track_par,
        "tpar": tpar,
        "cals": cals,
        "epar": epar,
        "n_cams": n_cams,
    }
    from types import SimpleNamespace
    exp = SimpleNamespace(**exp)
    py_sequence_loop(exp)
    return (seq_first, seq_last)

def chunk_ranges(first, last, n_chunks):
    """Split the frame range into n_chunks as evenly as possible."""
    first = int(first)
    last = int(last)
    total = last - first + 1
    chunk_size = total // n_chunks
    ranges = []
    for i in range(n_chunks):
        start = first + i * chunk_size
        end = start + chunk_size - 1 if i < n_chunks - 1 else last
        ranges.append((start, end))
    return ranges

def main(exp_path, first, last, n_processes=2):
    start = time.time()
    exp_path = Path(exp_path).resolve()
    print(f"Running in {exp_path}")
    os.chdir(exp_path)
    res_path = exp_path / "res"
    if not res_path.is_dir():
        print(" 'res' folder not found. creating one")
        res_path.mkdir(parents=True, exist_ok=True)

    ranges = chunk_ranges(first, last, n_processes)
    print(f"Frame chunks: {ranges}")

    with ProcessPoolExecutor(max_workers=n_processes) as executor:
        futures = []
        for seq_first, seq_last in ranges:
            futures.append(executor.submit(run_sequence_chunk, exp_path, seq_first, seq_last))
        for f in futures:
            try:
                result = f.result()
                print(f"Finished chunk: {result}")
            except Exception as e:
                print(f"Chunk failed: {e}")

    end = time.time()
    print("Total time elapsed: %f sec" % (end - start))

if __name__ == "__main__":
    print("inside pyptv_batch_parallel.py\n")
    print(sys.argv)
    if len(sys.argv) < 5:
        print(
            "Usage: python pyptv_batch_parallel.py experiments/exp1 seq_first seq_last n_processes"
        )
        exp_path = Path("tests/test_cavity").resolve()
        first = 10000
        last = 10004
        n_processes = 2
    else:
        exp_path = sys.argv[1]
        first = int(sys.argv[2])
        last = int(sys.argv[3])
        n_processes = int(sys.argv[4])
    main(exp_path, first, last, n_processes)