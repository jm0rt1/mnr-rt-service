"""
GTFS Data Downloader

This module provides functionality to download and update GTFS static data
from the MTA Metro-North Railroad feed. The downloader enforces rate limiting
to prevent excessive downloads.
"""

import zipfile
import shutil
import time
import logging
from pathlib import Path
from datetime import datetime
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class GTFSDownloader:
    """
    Downloads and updates GTFS static schedule data.
    
    The downloader:
    - Downloads GTFS ZIP files from a configured URL
    - Extracts files to a target directory
    - Enforces rate limiting (max 1 download per day by default)
    - Tracks last download time to prevent excessive API calls
    """
    
    # Default MTA Metro-North Railroad GTFS feed URL
    DEFAULT_GTFS_URL = "https://rrgtfsfeeds.s3.amazonaws.com/gtfsmnr.zip"
    
    # Minimum time between downloads (in seconds) - 1 day by default
    DEFAULT_MIN_DOWNLOAD_INTERVAL = 24 * 60 * 60  # 24 hours
    
    def __init__(
        self,
        gtfs_url: str = DEFAULT_GTFS_URL,
        output_dir: Optional[Path] = None,
        min_download_interval: int = DEFAULT_MIN_DOWNLOAD_INTERVAL,
        timestamp_file: Optional[Path] = None
    ):
        """
        Initialize the GTFS downloader.
        
        Args:
            gtfs_url: URL to download the GTFS ZIP file from
            output_dir: Directory to extract GTFS files to
            min_download_interval: Minimum seconds between downloads
            timestamp_file: File to store last download timestamp
        """
        self.gtfs_url = gtfs_url
        self.min_download_interval = min_download_interval
        
        # Set default output directory if not provided
        if output_dir is None:
            self.output_dir = Path("./gtfs/metro-north-railroad/gtfsmnr").resolve()
        else:
            self.output_dir = Path(output_dir).resolve()
        
        # Set timestamp file path
        if timestamp_file is None:
            self.timestamp_file = self.output_dir.parent / ".last_download"
        else:
            self.timestamp_file = Path(timestamp_file)
    
    def _get_last_download_time(self) -> Optional[float]:
        """
        Get the timestamp of the last download.
        
        Returns:
            Unix timestamp of last download, or None if never downloaded
        """
        if not self.timestamp_file.exists():
            return None
        
        try:
            with open(self.timestamp_file, 'r') as f:
                return float(f.read().strip())
        except (ValueError, IOError) as e:
            logger.warning(f"Could not read timestamp file: {e}")
            return None
    
    def _update_last_download_time(self):
        """Update the last download timestamp to current time."""
        try:
            self.timestamp_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.timestamp_file, 'w') as f:
                f.write(str(time.time()))
        except IOError as e:
            logger.error(f"Could not write timestamp file: {e}")
    
    def should_download(self, force: bool = False) -> bool:
        """
        Check if a download should be performed based on rate limiting.
        
        Args:
            force: If True, bypass rate limiting check
            
        Returns:
            True if download should proceed, False otherwise
        """
        if force:
            return True
        
        last_download = self._get_last_download_time()
        if last_download is None:
            return True
        
        time_since_last = time.time() - last_download
        return time_since_last >= self.min_download_interval
    
    def get_time_until_next_download(self) -> Optional[float]:
        """
        Get seconds until next download is allowed.
        
        Returns:
            Seconds until next download, 0 if download is allowed now,
            or None if never downloaded before
        """
        last_download = self._get_last_download_time()
        if last_download is None:
            return None
        
        time_since_last = time.time() - last_download
        time_remaining = self.min_download_interval - time_since_last
        return max(0, time_remaining)
    
    def download_and_extract(self, force: bool = False) -> bool:
        """
        Download and extract GTFS data.
        
        Args:
            force: If True, bypass rate limiting
            
        Returns:
            True if download succeeded, False otherwise
            
        Raises:
            ValueError: If download is not allowed due to rate limiting
        """
        # Check rate limiting
        if not self.should_download(force):
            time_remaining = self.get_time_until_next_download()
            hours_remaining = time_remaining / 3600
            raise ValueError(
                f"Download rate limit exceeded. "
                f"Next download allowed in {hours_remaining:.1f} hours"
            )
        
        logger.info(f"Downloading GTFS data from {self.gtfs_url}")
        
        # Create temporary directory for download
        temp_dir = self.output_dir.parent / ".gtfs_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_zip = temp_dir / "gtfs.zip"
        
        try:
            # Download the ZIP file
            response = requests.get(self.gtfs_url, timeout=60)
            response.raise_for_status()
            
            with open(temp_zip, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded {len(response.content)} bytes")
            
            # Extract the ZIP file
            logger.info(f"Extracting to {self.output_dir}")
            
            # Remove old data if it exists
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract all files
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(self.output_dir)
            
            logger.info("Extraction complete")
            
            # Update timestamp
            self._update_last_download_time()
            
            # Cleanup temp directory
            shutil.rmtree(temp_dir)
            
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to download GTFS data: {e}")
            # Cleanup on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return False
        except zipfile.BadZipFile as e:
            logger.error(f"Downloaded file is not a valid ZIP: {e}")
            # Cleanup on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return False
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            # Cleanup on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return False
    
    def get_download_info(self) -> dict:
        """
        Get information about the download status.
        
        Returns:
            Dictionary with download information
        """
        last_download = self._get_last_download_time()
        can_download = self.should_download()
        time_until_next = self.get_time_until_next_download()
        
        info = {
            'gtfs_url': self.gtfs_url,
            'output_dir': str(self.output_dir),
            'min_download_interval': self.min_download_interval,
            'can_download_now': can_download,
        }
        
        if last_download is not None:
            info['last_download'] = datetime.fromtimestamp(last_download).isoformat()
            if time_until_next is not None and time_until_next > 0:
                info['next_download_allowed_in_hours'] = round(time_until_next / 3600, 2)
        else:
            info['last_download'] = None
        
        return info
