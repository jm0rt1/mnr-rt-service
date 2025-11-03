import sys
import os
from PySide6.QtWidgets import QApplication
from .main_window import MainWindow


def main() -> int:
    # Ensure CWD is project root when running via debugger/launcher
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(os.path.dirname(project_root))

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()
