"""Main entry point for running PyPTV."""

import sys
import os
from pathlib import Path
import argparse

def main():
    """Parse arguments and launch appropriate interface."""
    parser = argparse.ArgumentParser(description="PyPTV - Python GUI for the OpenPTV library")
    parser.add_argument("path", nargs="?", help="Path to the experiment directory")
    parser.add_argument("--modern", action="store_true", help="Use the modern UI (default)")
    parser.add_argument("--legacy", action="store_true", help="Use the legacy UI")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--cli", action="store_true", help="Use command line interface")
    
    args = parser.parse_args()
    
    # Handle version request
    if args.version:
        from pyptv import __version__
        print(f"PyPTV version {__version__}")
        return
    
    # Check for CLI mode
    if args.cli:
        from pyptv import cli
        cli()
        return
    
    # Default to modern UI unless legacy is explicitly requested
    use_legacy = args.legacy and not args.modern
    
    # Get experiment path
    if args.path:
        exp_path = Path(args.path)
        if not exp_path.exists() or not exp_path.is_dir():
            print(f"Error: {exp_path} is not a valid directory")
            return
    else:
        exp_path = Path.cwd()
    
    print(f"Starting PyPTV with experiment path: {exp_path}")
    
    # Launch appropriate UI
    if use_legacy:
        print("Using legacy UI")
        import pyptv.pyptv_gui as gui
        # Set argv for legacy GUI
        sys.argv = [sys.argv[0]]
        if args.path:
            sys.argv.append(str(exp_path))
        gui.main()
    else:
        print("Using modern UI")
        from pyptv.ui.app import main as modern_main
        # Set argv for modern GUI
        sys.argv = [sys.argv[0]]
        if args.path:
            sys.argv.append(str(exp_path))
        modern_main()


if __name__ == "__main__":
    main()
