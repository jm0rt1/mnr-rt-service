"""
Unit tests for GTFS Downloader
"""

import unittest
import tempfile
import shutil
import time
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.gtfs_downloader import GTFSDownloader


class TestGTFSDownloader(unittest.TestCase):
    """Test cases for GTFSDownloader"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directories for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "gtfs_output"
        self.timestamp_file = self.temp_dir / "timestamp"
        
        # Create downloader instance
        self.downloader = GTFSDownloader(
            output_dir=self.output_dir,
            timestamp_file=self.timestamp_file,
            min_download_interval=60  # 1 minute for testing
        )

    def tearDown(self):
        """Clean up test fixtures"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_init_default_values(self):
        """Test initialization with default values"""
        downloader = GTFSDownloader()
        self.assertEqual(downloader.gtfs_url, GTFSDownloader.DEFAULT_GTFS_URL)
        self.assertEqual(
            downloader.min_download_interval,
            GTFSDownloader.DEFAULT_MIN_DOWNLOAD_INTERVAL
        )

    def test_init_custom_values(self):
        """Test initialization with custom values"""
        custom_url = "https://example.com/gtfs.zip"
        custom_interval = 3600
        
        downloader = GTFSDownloader(
            gtfs_url=custom_url,
            output_dir=self.output_dir,
            min_download_interval=custom_interval
        )
        
        self.assertEqual(downloader.gtfs_url, custom_url)
        self.assertEqual(downloader.min_download_interval, custom_interval)
        self.assertEqual(downloader.output_dir, self.output_dir)

    def test_get_last_download_time_no_file(self):
        """Test getting last download time when file doesn't exist"""
        result = self.downloader._get_last_download_time()
        self.assertIsNone(result)

    def test_update_last_download_time(self):
        """Test updating the last download timestamp"""
        before = time.time()
        self.downloader._update_last_download_time()
        after = time.time()
        
        # Check that file was created
        self.assertTrue(self.timestamp_file.exists())
        
        # Check that timestamp is reasonable
        timestamp = self.downloader._get_last_download_time()
        self.assertIsNotNone(timestamp)
        self.assertGreaterEqual(timestamp, before)
        self.assertLessEqual(timestamp, after)

    def test_should_download_never_downloaded(self):
        """Test should_download returns True when never downloaded"""
        result = self.downloader.should_download()
        self.assertTrue(result)

    def test_should_download_within_interval(self):
        """Test should_download returns False within rate limit interval"""
        # Simulate a recent download
        self.downloader._update_last_download_time()
        
        # Should not allow download immediately
        result = self.downloader.should_download()
        self.assertFalse(result)

    def test_should_download_after_interval(self):
        """Test should_download returns True after rate limit interval"""
        # Simulate a download from the past
        past_time = time.time() - 120  # 2 minutes ago
        with open(self.timestamp_file, 'w') as f:
            f.write(str(past_time))
        
        # Should allow download (interval is 60 seconds)
        result = self.downloader.should_download()
        self.assertTrue(result)

    def test_should_download_force(self):
        """Test should_download with force=True bypasses rate limit"""
        # Simulate a recent download
        self.downloader._update_last_download_time()
        
        # Should allow download with force=True
        result = self.downloader.should_download(force=True)
        self.assertTrue(result)

    def test_get_time_until_next_download_never_downloaded(self):
        """Test time until next download when never downloaded"""
        result = self.downloader.get_time_until_next_download()
        self.assertIsNone(result)

    def test_get_time_until_next_download_recent(self):
        """Test time until next download after recent download"""
        # Simulate a download 30 seconds ago
        past_time = time.time() - 30
        with open(self.timestamp_file, 'w') as f:
            f.write(str(past_time))
        
        # Should have ~30 seconds remaining (interval is 60 seconds)
        result = self.downloader.get_time_until_next_download()
        self.assertIsNotNone(result)
        self.assertGreater(result, 0)
        self.assertLess(result, 60)

    def test_get_time_until_next_download_ready(self):
        """Test time until next download when ready"""
        # Simulate a download from the past
        past_time = time.time() - 120
        with open(self.timestamp_file, 'w') as f:
            f.write(str(past_time))
        
        # Should return 0 (ready to download)
        result = self.downloader.get_time_until_next_download()
        self.assertEqual(result, 0)

    @patch('src.gtfs_downloader.requests.get')
    def test_download_and_extract_success(self, mock_get):
        """Test successful download and extraction"""
        # Create a mock ZIP file content
        mock_zip_content = self._create_test_zip()
        
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.content = mock_zip_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Perform download
        result = self.downloader.download_and_extract(force=True)
        
        # Verify success
        self.assertTrue(result)
        
        # Verify files were extracted
        self.assertTrue(self.output_dir.exists())
        self.assertTrue((self.output_dir / "test_file.txt").exists())
        
        # Verify timestamp was updated
        self.assertTrue(self.timestamp_file.exists())
        
        # Verify content
        with open(self.output_dir / "test_file.txt", 'r') as f:
            content = f.read()
            self.assertEqual(content, "test content")

    @patch('src.gtfs_downloader.requests.get')
    def test_download_and_extract_rate_limited(self, mock_get):
        """Test download respects rate limiting"""
        # Simulate a recent download
        self.downloader._update_last_download_time()
        
        # Attempt download without force
        with self.assertRaises(ValueError) as context:
            self.downloader.download_and_extract(force=False)
        
        self.assertIn("rate limit", str(context.exception).lower())

    @patch('src.gtfs_downloader.requests.get')
    def test_download_and_extract_http_error(self, mock_get):
        """Test download handles HTTP errors gracefully"""
        # Mock HTTP error
        mock_get.side_effect = Exception("Network error")
        
        # Perform download
        result = self.downloader.download_and_extract(force=True)
        
        # Verify failure
        self.assertFalse(result)

    @patch('src.gtfs_downloader.requests.get')
    def test_download_and_extract_invalid_zip(self, mock_get):
        """Test download handles invalid ZIP files"""
        # Mock response with invalid ZIP content
        mock_response = Mock()
        mock_response.content = b"not a zip file"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Perform download
        result = self.downloader.download_and_extract(force=True)
        
        # Verify failure
        self.assertFalse(result)

    @patch('src.gtfs_downloader.requests.get')
    def test_download_replaces_existing_data(self, mock_get):
        """Test download replaces existing GTFS data"""
        # Create existing data
        self.output_dir.mkdir(parents=True)
        old_file = self.output_dir / "old_file.txt"
        with open(old_file, 'w') as f:
            f.write("old data")
        
        # Create new ZIP content
        mock_zip_content = self._create_test_zip()
        mock_response = Mock()
        mock_response.content = mock_zip_content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Perform download
        result = self.downloader.download_and_extract(force=True)
        
        # Verify success
        self.assertTrue(result)
        
        # Verify old file is gone
        self.assertFalse(old_file.exists())
        
        # Verify new file exists
        self.assertTrue((self.output_dir / "test_file.txt").exists())

    def test_get_download_info_never_downloaded(self):
        """Test get_download_info when never downloaded"""
        info = self.downloader.get_download_info()
        
        self.assertEqual(info['gtfs_url'], self.downloader.gtfs_url)
        self.assertEqual(info['output_dir'], str(self.output_dir))
        self.assertEqual(info['min_download_interval'], 60)
        self.assertTrue(info['can_download_now'])
        self.assertIsNone(info['last_download'])

    def test_get_download_info_after_download(self):
        """Test get_download_info after a download"""
        # Simulate a download 30 seconds ago
        past_time = time.time() - 30
        with open(self.timestamp_file, 'w') as f:
            f.write(str(past_time))
        
        info = self.downloader.get_download_info()
        
        self.assertFalse(info['can_download_now'])
        self.assertIsNotNone(info['last_download'])
        self.assertIn('next_download_allowed_in_hours', info)

    def _create_test_zip(self) -> bytes:
        """Create a test ZIP file in memory and return its bytes"""
        import io
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("test_file.txt", "test content")
        
        return zip_buffer.getvalue()


if __name__ == '__main__':
    unittest.main()
