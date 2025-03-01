"""Application entry point for the modernized PyPTV UI."""

import sys
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

from pyptv import __version__
from pyptv.ui.main_window import MainWindow


def main():
    """Main function to start the application."""
    # Clean sys.argv of flags that have been handled in pyptv_gui.py
    if '--modern' in sys.argv:
        sys.argv.remove('--modern')
        
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("PyPTV")
    app.setApplicationVersion(__version__)
    
    # Parse command line args
    exp_path = './tests/test_cavity'
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        path = Path(sys.argv[1])
        if path.exists() and path.is_dir():
            exp_path = path
    
    # Create and show the main window
    window = MainWindow(exp_path=exp_path)
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    main()