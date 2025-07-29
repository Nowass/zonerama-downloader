"""
Main downloader module for Zonerama Downloader

Contains the core ZoneramaDownloader class that orchestrates the download process
"""

import time
from pathlib import Path

from .config import Config
from .cli import display_configuration, get_user_input, confirm_action
from .file_utils import (
    ensure_directory_exists, is_album_already_downloaded, 
    list_zip_files, unzip_file, sanitize_filename
)
from .scraper import ZoneramaScraper


class ZoneramaDownloader:
    """Main downloader class that orchestrates the album download process"""
    
    def __init__(self, config):
        """Initialize the downloader with configuration
        
        Args:
            config (Config): Configuration object
        """
        self.config = config
        self.scraper = ZoneramaScraper(config)
        
        # Statistics
        self.albums_processed = 0
        self.albums_downloaded = 0
        self.albums_skipped = 0
        self.albums_failed = 0
    
    def setup(self):
        """Setup the downloader (create directories, initialize scraper)
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            # Ensure download directory exists
            ensure_directory_exists(self.config.absolute_download_dir)
            
            # Setup web scraper
            if not self.scraper.setup_driver():
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error during setup: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        self.scraper.close_driver()
    
    def run(self):
        """Main method to run the download process
        
        Returns:
            bool: True if completed successfully, False if there were critical errors
        """
        try:
            # Display configuration
            display_configuration(self.config)
            
            # Wait for user confirmation
            get_user_input()
            
            # Setup
            if not self.setup():
                return False
            
            # Navigate to albums page
            if not self.scraper.navigate_to_albums():
                return False
            
            # Handle cookie modal
            self.scraper.handle_cookie_modal()
            
            # Find and process albums
            success = self._process_all_albums()
            
            # Post-process downloaded files if unzipping is enabled
            if success and self.config.unzip:
                self._unzip_all_albums()
            
            # Display final statistics
            self._display_final_statistics()
            
            return success
            
        except KeyboardInterrupt:
            print("\n🛑 Download interrupted by user.")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        finally:
            self.cleanup()
    
    def _process_all_albums(self):
        """Process all albums on the page
        
        Returns:
            bool: True if processing completed, False if critical error
        """
        albums = self.scraper.find_album_elements()
        
        if not albums:
            print("📭 No albums found to download.")
            return True
        
        print(f"\n🎯 Starting to process {len(albums)} albums...")
        print("=" * 60)
        
        for i, album_data in enumerate(albums, 1):
            try:
                album_name = self.scraper.get_album_name(album_data)
                album_url = album_data['href']
                self.albums_processed += 1
                
                print(f"\n📂 [{i}/{len(albums)}] Processing: {album_name}")
                
                # Check if already downloaded
                if is_album_already_downloaded(self.config.absolute_download_dir, album_name):
                    print(f"⏭️  Album '{album_name}' already exists, skipping...")
                    self.albums_skipped += 1
                    continue
                
                # Download the album
                if self._download_single_album(album_url, album_name):
                    self.albums_downloaded += 1
                    print(f"✅ Successfully downloaded: {album_name}")
                else:
                    self.albums_failed += 1
                    print(f"❌ Failed to download: {album_name}")
                
                # Brief pause between downloads
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing album {i}: {e}")
                self.albums_failed += 1
                continue
        
        return True
    
    def _download_single_album(self, album_url, album_name):
        """Download a single album
        
        Args:
            album_url (str): URL of the album
            album_name (str): Name of the album
            
        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            # Navigate to album page
            if not self.scraper.navigate_to_album(album_url):
                return False
            
            # Wait for and click download button
            download_button = self.scraper.wait_for_download_button()
            if not download_button:
                self.scraper.navigate_back()
                return False
            
            if not self.scraper.click_download_button(download_button):
                self.scraper.navigate_back()
                return False
            
            # Handle download modal
            if not self.scraper.handle_download_modal():
                self.scraper.navigate_back()
                return False
            
            # Wait for download to complete
            print(f"⏳ Waiting for download to complete...")
            sanitized_name = sanitize_filename(album_name)
            success, filepath = self.scraper.wait_for_download_completion(sanitized_name)
            
            if success:
                print(f"💾 Download completed: {filepath}")
            else:
                print(f"❌ Download timeout for album: {album_name}")
            
            # Navigate back to albums list
            if not self.scraper.navigate_back():
                print("⚠️  Warning: Could not navigate back, continuing...")
            
            return success
            
        except Exception as e:
            print(f"❌ Error downloading album '{album_name}': {e}")
            # Try to navigate back on error
            try:
                self.scraper.navigate_back()
            except Exception:
                pass
            return False
    
    def _unzip_all_albums(self):
        """Unzip all downloaded ZIP files"""
        print("\n" + "=" * 60)
        print("📦 UNZIPPING DOWNLOADED ALBUMS")
        print("=" * 60)
        
        zip_files = list_zip_files(self.config.absolute_download_dir)
        
        if not zip_files:
            print("📭 No ZIP files found to unzip.")
            return
        
        print(f"🔍 Found {len(zip_files)} ZIP files to process...")
        
        successful_extractions = 0
        failed_extractions = 0
        
        for i, zip_path in enumerate(zip_files, 1):
            zip_file = Path(zip_path)
            print(f"\n📦 [{i}/{len(zip_files)}] Unzipping: {zip_file.name}")
            
            success, extract_path, error = unzip_file(
                str(zip_file),
                self.config.absolute_download_dir,
                delete_after=self.config.delete_zips
            )
            
            if success:
                successful_extractions += 1
                action = "and deleted ZIP" if self.config.delete_zips else ""
                print(f"✅ Extracted to: {extract_path} {action}")
            else:
                failed_extractions += 1
                print(f"❌ Failed to extract: {error}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📦 UNZIPPING SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully extracted: {successful_extractions}")
        print(f"❌ Failed extractions: {failed_extractions}")
        
        if self.config.delete_zips and successful_extractions > 0:
            print(f"🗑️  ZIP files deleted after extraction")
    
    def _display_final_statistics(self):
        """Display final download statistics"""
        print("\n" + "=" * 60)
        print("📊 DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"📂 Albums processed: {self.albums_processed}")
        print(f"✅ Successfully downloaded: {self.albums_downloaded}")
        print(f"⏭️  Already existed (skipped): {self.albums_skipped}")
        print(f"❌ Failed downloads: {self.albums_failed}")
        
        if self.albums_downloaded > 0:
            print(f"📁 Downloads saved to: {self.config.absolute_download_dir}")
        
        print("=" * 60)
        
        if self.albums_downloaded > 0:
            print("🎉 Download process completed successfully!")
        elif self.albums_skipped > 0 and self.albums_failed == 0:
            print("ℹ️  All albums were already downloaded.")
        else:
            print("⚠️  Download process completed with issues.")
