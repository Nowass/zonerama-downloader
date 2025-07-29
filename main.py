"""
Main entry point for Zonerama Downloader

This is the new modular version of the application
"""

import sys
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.cli import parse_arguments
from src.config import Config
from src.downloader import ZoneramaDownloader


def main():
    """Main entry point for the application"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Create configuration with user arguments
        config = Config(
            download_dir=args.download_dir,
            unzip=args.unzip,
            delete_zips=args.delete
        )
        
        # Create and run downloader
        downloader = ZoneramaDownloader(config)
        success = downloader.run()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user.")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
