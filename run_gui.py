#!/usr/bin/env python3
"""
Alternative entry point for the GUI - redirects to gui_app.py

For consistency, it's recommended to use gui_app.py directly.
This file is kept for backwards compatibility.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main GUI application
from gui_app import main

if __name__ == "__main__":
    raise SystemExit(main())
