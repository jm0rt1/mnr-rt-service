"""
Legacy app module - redirects to the proper controller-based implementation.

This module is deprecated. Use gui_app.py at the project root instead.
Kept for backwards compatibility with older code.
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


def main() -> int:
    """Main entry point - uses the full-featured MainWindowController"""
    logger.info("Starting MNR Real-Time Service Manager GUI (via legacy app.py)")
    
    # Create the Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("MNR Real-Time Service Manager")
    app.setOrganizationName("MNR")
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create and show the main window (using the proper controller)
    window = MainWindowController()
    window.show()
    
    logger.info("GUI initialized successfully")
    
    # Run the application
    exit_code = app.exec()
    
    logger.info(f"GUI exiting with code {exit_code}")
    return exit_code
