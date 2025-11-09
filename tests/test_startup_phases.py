#!/usr/bin/env python3
"""
Tests for server startup phase detection and progress tracking.
"""

import unittest
import subprocess
import sys
import time
from pathlib import Path


class TestStartupPhases(unittest.TestCase):
    """Test that startup phases are correctly reported"""
    
    def test_startup_phases_present(self):
        """Test that all expected startup phases are present in server output"""
        # Find web_server.py
        project_root = Path(__file__).parent.parent
        web_server_path = project_root / "web_server.py"
        
        self.assertTrue(web_server_path.exists(), "web_server.py not found")
        
        # Expected phases when skipping GTFS update
        expected_phases = [
            'STARTUP_PHASE: INITIALIZING',
            'STARTUP_PHASE: GTFS_CHECK_SKIPPED',
            'STARTUP_PHASE: CLIENT_INIT',
            'STARTUP_PHASE: GTFS_LOAD',
            'STARTUP_PHASE: SERVER_START',
            'STARTUP_PHASE: READY'
        ]
        
        # Start server process with skip-gtfs-update
        # Use a timeout to prevent hanging
        try:
            result = subprocess.run(
                [sys.executable, str(web_server_path), '--port', '0', '--skip-gtfs-update'],
                capture_output=True,
                text=True,
                timeout=10
            )
        except subprocess.TimeoutExpired as e:
            # Timeout is expected since Flask will keep running
            output = e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout
        else:
            output = result.stdout
        
        # Check that all expected phases are in the output
        for phase in expected_phases:
            self.assertIn(phase, output, f"Expected phase '{phase}' not found in output")
        
        # Verify they appear in order
        positions = [output.find(phase) for phase in expected_phases]
        self.assertEqual(positions, sorted(positions), 
                        "Startup phases are not in expected order")
    
    def test_gtfs_check_phase_when_not_skipped(self):
        """Test that GTFS_CHECK phase appears when not skipped"""
        project_root = Path(__file__).parent.parent
        web_server_path = project_root / "web_server.py"
        
        # Start server process WITHOUT skip-gtfs-update
        try:
            result = subprocess.run(
                [sys.executable, str(web_server_path), '--port', '0'],
                capture_output=True,
                text=True,
                timeout=15
            )
        except subprocess.TimeoutExpired as e:
            output = e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout
        else:
            output = result.stdout
        
        # Should have GTFS_CHECK phase
        self.assertIn('STARTUP_PHASE: GTFS_CHECK', output,
                     "GTFS_CHECK phase should be present when not skipped")


if __name__ == '__main__':
    unittest.main()
