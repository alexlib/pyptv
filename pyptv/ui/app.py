"""Application entry point for the modernized PyPTV UI."""

import sys
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

from pyptv import __version__
from pyptv.ui.main_window import MainWindow


def main():
    """Main function to start the application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("PyPTV")
    app.setApplicationVersion(__version__)
    
    # Parse command line args
    exp_path = None
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if path.exists() and path.is_dir():
            exp_path = path
    
    # Create and show the main window
    window = MainWindow(exp_path=exp_path)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()