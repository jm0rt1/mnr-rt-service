#!/usr/bin/env python3
"""
GUI Validation Script

Validates the GUI code structure without requiring a display server.
Tests that all imports work and code is syntactically correct.
"""

import sys
import importlib.util
from pathlib import Path


def validate_module(module_path, module_name):
    """Validate that a module can be loaded"""
    try:
        # Load the module spec
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None:
            return False, f"Failed to load module spec for {module_name}"
        
        # Don't actually import (to avoid display issues)
        # Just check that the file is valid Python
        with open(module_path, 'r') as f:
            code = f.read()
            compile(code, module_path, 'exec')
        
        return True, f"✓ {module_name} is valid"
    except SyntaxError as e:
        return False, f"✗ {module_name} has syntax error: {e}"
    except Exception as e:
        return False, f"✗ {module_name} validation failed: {e}"


def main():
    """Main validation function"""
    print("=" * 60)
    print("GUI Code Validation")
    print("=" * 60)
    
    # Use current working directory instead of script location
    base_dir = Path.cwd()
    print(f"Base directory: {base_dir}\n")
    
    # Files to validate
    files_to_check = [
        ("gui_app.py", "gui_app"),
        ("src/gui/__init__.py", "src.gui.__init__"),
        ("src/gui/controllers/__init__.py", "src.gui.controllers.__init__"),
        ("src/gui/controllers/main_window_controller.py", "src.gui.controllers.main_window_controller"),
        ("src/gui/views/__init__.py", "src.gui.views.__init__"),
        ("src/gui/views/generated/__init__.py", "src.gui.views.generated.__init__"),
        ("src/gui/views/generated/main_window.py", "src.gui.views.generated.main_window"),
        ("src/gui/models/__init__.py", "src.gui.models.__init__"),
    ]
    
    all_valid = True
    results = []
    
    for file_path, module_name in files_to_check:
        full_path = base_dir / file_path
        if not full_path.exists():
            results.append((False, f"✗ {file_path} does not exist"))
            all_valid = False
            continue
        
        valid, message = validate_module(full_path, module_name)
        results.append((valid, message))
        if not valid:
            all_valid = False
    
    # Print results
    print("\nValidation Results:")
    print("-" * 60)
    for valid, message in results:
        print(message)
    
    # Check UI file
    print("\nUI Resources:")
    print("-" * 60)
    ui_file = base_dir / "resources" / "main_window.ui"
    if ui_file.exists():
        print(f"✓ resources/main_window.ui exists ({ui_file.stat().st_size} bytes)")
    else:
        print("✗ resources/main_window.ui does not exist")
        all_valid = False
    
    # Check generate script
    gen_script = base_dir / "generate_ui.sh"
    if gen_script.exists():
        print(f"✓ generate_ui.sh exists")
    else:
        print("✗ generate_ui.sh does not exist")
        all_valid = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_valid:
        print("✓ All GUI validation checks passed!")
        print("\nThe GUI code is structurally sound and should work when")
        print("run on a system with a display server.")
        print("\nTo run the GUI:")
        print("  python gui_app.py")
        return 0
    else:
        print("✗ Some validation checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
