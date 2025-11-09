#!/usr/bin/env python3
"""
Test GUI Controller Endpoint Methods

Tests the new endpoint methods added to the GUI controller without
requiring a display server.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGUIControllerMethods(unittest.TestCase):
    """Test GUI controller has all required methods"""
    
    def test_controller_has_endpoint_methods(self):
        """Test that MainWindowController has methods for all endpoints"""
        # We can't actually instantiate the controller without a display,
        # but we can check that the methods exist in the source code
        controller_file = Path(__file__).parent.parent / 'src' / 'gui' / 'controllers' / 'main_window_controller.py'
        
        with open(controller_file, 'r') as f:
            source_code = f.read()
        
        # Check for required methods
        required_methods = [
            'refresh_stations_data',
            'refresh_routes_data',
            'refresh_travel_data',
            'refresh_api_info',
            '_setup_additional_tabs'
        ]
        
        for method in required_methods:
            self.assertIn(f'def {method}(', source_code, 
                         f"Method {method} not found in controller")
    
    def test_controller_has_new_ui_elements(self):
        """Test that controller creates new UI elements"""
        controller_file = Path(__file__).parent.parent / 'src' / 'gui' / 'controllers' / 'main_window_controller.py'
        
        with open(controller_file, 'r') as f:
            source_code = f.read()
        
        # Check for new tab widgets
        required_elements = [
            'stationsTab',
            'routesTab',
            'travelTab',
            'apiInfoTab',
            'stationsTable',
            'routesTable',
            'locationText',
            'distanceText',
            'nextTrainText',
            'arduinoText',
            'apiInfoText'
        ]
        
        for element in required_elements:
            self.assertIn(f'self.{element}', source_code, 
                         f"UI element {element} not found in controller")
    
    def test_controller_adds_tabs_to_widget(self):
        """Test that controller adds tabs to the main tab widget"""
        controller_file = Path(__file__).parent.parent / 'src' / 'gui' / 'controllers' / 'main_window_controller.py'
        
        with open(controller_file, 'r') as f:
            source_code = f.read()
        
        # Check that tabs are added
        expected_tabs = [
            '"Stations"',
            '"Routes"',
            '"Travel Assistance"',
            '"API Information"'
        ]
        
        for tab_name in expected_tabs:
            self.assertIn(f'addTab', source_code)
            self.assertIn(tab_name, source_code, 
                         f"Tab {tab_name} not added to tab widget")
    
    def test_controller_imports_required_widgets(self):
        """Test that controller imports all required Qt widgets"""
        controller_file = Path(__file__).parent.parent / 'src' / 'gui' / 'controllers' / 'main_window_controller.py'
        
        with open(controller_file, 'r') as f:
            source_code = f.read()
        
        # Check for required imports
        required_imports = [
            'QWidget',
            'QVBoxLayout',
            'QHBoxLayout',
            'QPushButton',
            'QLabel',
            'QTableWidget',
            'QHeaderView',
            'QTextEdit',
            'QGroupBox'
        ]
        
        for import_name in required_imports:
            self.assertIn(import_name, source_code, 
                         f"Import {import_name} not found in controller")


class TestGUIEndpointIntegration(unittest.TestCase):
    """Test that GUI endpoint methods properly integrate with web server"""
    
    def test_stations_endpoint_url_format(self):
        """Test that stations refresh uses correct endpoint URL"""
        controller_file = Path(__file__).parent.parent / 'src' / 'gui' / 'controllers' / 'main_window_controller.py'
        
        with open(controller_file, 'r') as f:
            source_code = f.read()
        
        # Check for correct endpoint URL
        self.assertIn('/stations', source_code, 
                     "Stations endpoint URL not found")
    
    def test_routes_endpoint_url_format(self):
        """Test that routes refresh uses correct endpoint URL"""
        controller_file = Path(__file__).parent.parent / 'src' / 'gui' / 'controllers' / 'main_window_controller.py'
        
        with open(controller_file, 'r') as f:
            source_code = f.read()
        
        # Check for correct endpoint URL
        self.assertIn('/routes', source_code, 
                     "Routes endpoint URL not found")
    
    def test_travel_endpoints_url_format(self):
        """Test that travel endpoints use correct URLs"""
        controller_file = Path(__file__).parent.parent / 'src' / 'gui' / 'controllers' / 'main_window_controller.py'
        
        with open(controller_file, 'r') as f:
            source_code = f.read()
        
        # Check for correct travel endpoint URLs
        travel_endpoints = [
            '/travel/location',
            '/travel/distance',
            '/travel/next-train',
            '/travel/arduino-device'
        ]
        
        for endpoint in travel_endpoints:
            self.assertIn(endpoint, source_code, 
                         f"Travel endpoint {endpoint} not found")
    
    def test_api_info_endpoint_url_format(self):
        """Test that API info uses root endpoint"""
        controller_file = Path(__file__).parent.parent / 'src' / 'gui' / 'controllers' / 'main_window_controller.py'
        
        with open(controller_file, 'r') as f:
            source_code = f.read()
        
        # Check that root endpoint is used in API info method
        # Look for the refresh_api_info method
        self.assertIn('def refresh_api_info', source_code)
        # The root endpoint should be accessed with just "/"
        self.assertIn('http://localhost', source_code)


if __name__ == '__main__':
    unittest.main()
