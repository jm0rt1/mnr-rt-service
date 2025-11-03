#!/usr/bin/env python3
"""
GTFS Update Utility

Command-line tool to download and update GTFS static schedule data.

Usage:
    python update_gtfs.py              # Download if needed (respects rate limit)
    python update_gtfs.py --force      # Force download (bypass rate limit)
    python update_gtfs.py --info       # Show download status
"""

import argparse
import sys
import logging
from src.gtfs_downloader import GTFSDownloader
from src.shared.settings import GlobalSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for GTFS update utility."""
    parser = argparse.ArgumentParser(
        description='Download and update GTFS static schedule data'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force download (bypass rate limiting)'
    )
    parser.add_argument(
        '--info',
        action='store_true',
        help='Show download status information only'
    )
    
    args = parser.parse_args()
    
    # Initialize downloader with settings
    downloader = GTFSDownloader(
        gtfs_url=GlobalSettings.GTFSDownloadSettings.GTFS_FEED_URL,
        output_dir=GlobalSettings.GTFS_MNR_DATA_DIR,
        min_download_interval=GlobalSettings.GTFSDownloadSettings.MIN_DOWNLOAD_INTERVAL
    )
    
    # Show info if requested
    if args.info:
        info = downloader.get_download_info()
        print("\n=== GTFS Download Status ===")
        print(f"Feed URL: {info['gtfs_url']}")
        print(f"Output Directory: {info['output_dir']}")
        print(f"Minimum Download Interval: {info['min_download_interval'] / 3600:.1f} hours")
        print(f"Can Download Now: {info['can_download_now']}")
        
        if info['last_download']:
            print(f"Last Download: {info['last_download']}")
            if 'next_download_allowed_in_hours' in info:
                print(f"Next Download Available In: {info['next_download_allowed_in_hours']:.2f} hours")
        else:
            print("Last Download: Never")
        
        print()
        return 0
    
    # Attempt download
    try:
        logger.info("Starting GTFS data update...")
        
        if not downloader.should_download(force=args.force) and not args.force:
            time_remaining = downloader.get_time_until_next_download()
            hours = time_remaining / 3600
            logger.info(
                f"Download not needed yet. Next download available in {hours:.1f} hours. "
                f"Use --force to override."
            )
            return 0
        
        success = downloader.download_and_extract(force=args.force)
        
        if success:
            logger.info("GTFS data updated successfully!")
            return 0
        else:
            logger.error("GTFS data update failed. Check logs for details.")
            return 1
            
    except ValueError as e:
        logger.error(f"Update blocked: {e}")
        logger.info("Use --force to override rate limiting")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
