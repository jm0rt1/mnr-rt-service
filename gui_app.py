#!/usr/bin/env python3
"""
MNR Real-Time Service Manager GUI

A graphical user interface for managing the Metro-North Railroad real-time service.
Provides server control, configuration, GTFS data management, and train data visualization.

Usage:
    python gui_app.py
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.gui.controllers.main_window_controller import MainWindowController
from src.shared.settings import GlobalSettings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(GlobalSettings.UI_LOGS_DIR / 'gui.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the GUI application"""
    logger.info("Starting MNR Real-Time Service Manager GUI")
    
    # Create the Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("MNR Real-Time Service Manager")
    app.setOrganizationName("MNR")
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create and show the main window
    window = MainWindowController()
    window.show()
    
    logger.info("GUI initialized successfully")
    
    # Run the application
    exit_code = app.exec()
    
    logger.info(f"GUI exiting with code {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
