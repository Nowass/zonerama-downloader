"""
Command Line Interface module for Zonerama Downloader

Handles argument parsing and CLI interactions
"""

import argparse
import sys
from .config import Config


def parse_arguments():
    """Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    # Handle special combined flags like -ud
    processed_args = []
    for arg in sys.argv[1:]:
        if arg == '-ud':
            # Expand -ud to -u --delete
            processed_args.extend(['-u', '--delete'])
        else:
            processed_args.append(arg)
    
    parser = argparse.ArgumentParser(
        description=f'{Config.APP_NAME} - {Config.DESCRIPTION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py
  python3 main.py --download-dir ~/Downloads/Zonerama
  python3 main.py -d /path/to/downloads
  python3 main.py -u                    # Download and unzip
  python3 main.py -ud                   # Download, unzip and delete ZIP files
  python3 main.py --unzip --delete      # Same as -ud (long form)
        """
    )
    
    parser.add_argument(
        '-d', '--download-dir',
        type=str,
        default=Config.DEFAULT_DOWNLOAD_DIR,
        help=f'Download directory path (default: {Config.DEFAULT_DOWNLOAD_DIR})'
    )
    
    parser.add_argument(
        '-u', '--unzip',
        action='store_true',
        help='Automatically unzip downloaded albums after download completes'
    )
    
    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete ZIP files after successful unzipping (requires --unzip/-u)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'{Config.APP_NAME} {Config.VERSION}'
    )
    
    # Parse the processed arguments
    args = parser.parse_args(processed_args)
    
    # Validate argument combinations
    if args.delete and not args.unzip:
        parser.error("--delete requires --unzip/-u to be specified. Use -ud or --unzip --delete")
    
    return args


def display_configuration(config):
    """Display current configuration to user
    
    Args:
        config (Config): Configuration object
    """
    print("=" * 60)
    print(f"🔽 {Config.APP_NAME}")
    print("=" * 60)
    print(f"📁 Download directory: {config.absolute_download_dir}")
    
    if config.unzip:
        if config.delete_zips:
            print("📦 Auto-unzip: ✅ ENABLED (with ZIP deletion)")
        else:
            print("📦 Auto-unzip: ✅ ENABLED")
    else:
        print("📦 Auto-unzip: ❌ DISABLED (use -u to enable)")
    
    print("=" * 60)


def get_user_input(prompt="Press Enter to continue..."):
    """Get user input with proper handling
    
    Args:
        prompt (str): Prompt to display to user
        
    Returns:
        str: User input
    """
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user.")
        raise


def confirm_action(message, default=False):
    """Ask user for confirmation
    
    Args:
        message (str): Confirmation message
        default (bool): Default response if user just presses Enter
        
    Returns:
        bool: True if user confirms, False otherwise
    """
    suffix = " (Y/n)" if default else " (y/N)"
    try:
        response = input(f"{message}{suffix}: ").strip().lower()
        if not response:
            return default
        return response.startswith('y')
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user.")
        return False
