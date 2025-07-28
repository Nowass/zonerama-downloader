import os
import time
import requests
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin, urlparse
import zipfile
import tempfile
import unicodedata

def parse_arguments():
    """Parse command line arguments"""
    import sys
    
    # Handle special combined flags like -ud
    processed_args = []
    for arg in sys.argv[1:]:
        if arg == '-ud':
            # Expand -ud to -u --delete
            processed_args.extend(['-u', '--delete'])
        else:
            processed_args.append(arg)
    
    parser = argparse.ArgumentParser(
        description='Zonerama Album Downloader - Download albums from Zonerama.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 zonerama-downloader.py
  python3 zonerama-downloader.py --download-dir ~/Downloads/Zonerama
  python3 zonerama-downloader.py -d /path/to/downloads
  python3 zonerama-downloader.py -u                    # Download and unzip
  python3 zonerama-downloader.py -ud                   # Download, unzip and delete ZIP files
  python3 zonerama-downloader.py --unzip --delete      # Same as -ud (long form)
        """
    )
    
    parser.add_argument(
        '-d', '--download-dir',
        type=str,
        default='downloads',
        help='Download directory path (default: downloads)'
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
        version='Zonerama Downloader 1.0.0'
    )
    
    # Parse the processed arguments
    args = parser.parse_args(processed_args)
    
    # Validate argument combinations
    if args.delete and not args.unzip:
        parser.error("--delete requires --unzip/-u to be specified. Use -ud or --unzip --delete")
    
    return args

class ZoneramaDownloader:
    def __init__(self, download_dir="downloads"):
        self.download_dir = download_dir
        self.driver = None
        self.session = requests.Session()
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
    
    def remove_diacritics(self, text):
        """Remove diacritics/accents from text to match filesystem naming"""
        if not text:
            return text
        
        # Normalize to decomposed form (NFD) and remove combining characters
        normalized = unicodedata.normalize('NFD', text)
        # Filter out combining characters (diacritics)
        without_diacritics = ''.join(char for char in normalized 
                                   if unicodedata.category(char) != 'Mn')
        return without_diacritics
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Remove headless mode to allow manual login
        # chrome_options.add_argument("--headless")
        
        # Set download preferences
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def wait_for_login(self):
        """Open Zonerama and wait for user to login manually"""
        print("Opening Zonerama login page...")
        self.driver.get("https://eu.zonerama.com/")
        
        print("Please login manually in the browser window.")
        print("After logging in, press Enter to continue...")
        input()
        
        # Skip login verification and assume user is logged in
        print("Proceeding with assumption that login was successful...")
        return True
    
    def navigate_to_hidden_albums(self):
        """Navigate to 'Skryta alba' (Hidden Albums) section"""
        try:
            print("Navigating directly to hidden albums...")
            # Use the direct URL you provided
            self.driver.get("https://eu.zonerama.com/POLeNo/57348?secret=2D2359641FEE4833A68BD152F809DF1E")
            
            # Wait for page to load
            time.sleep(3)
            print("Navigated to hidden albums section")
            return True
            
        except Exception as e:
            print(f"Error navigating to hidden albums: {e}")
            return False
    
    def get_album_links(self):
        """Extract all album links from the current page"""
        try:
            # Wait a bit for page to load
            time.sleep(3)
            
            # Navigation links to skip
            skip_patterns = [
                'Veřejná alba',
                'Skrytá alba',
                'Public albums',
                'Hidden albums',
                'inzerce',
                'advertisement'
            ]
            
            # Common selectors for album links
            album_selectors = [
                "a[href*='/album/']",
                "a[href*='/POLeNo/']",
                ".album-link",
                ".album-item a",
                "[data-testid='album-link']",
                "a[title]"  # Generic link with title
            ]
            
            albums = []
            for selector in album_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        for element in elements:
                            href = element.get_attribute('href')
                            title = element.get_attribute('title') or element.text.strip()
                            
                            # Skip navigation links
                            skip_this = False
                            for skip_pattern in skip_patterns:
                                if skip_pattern.lower() in title.lower():
                                    print(f"Skipping navigation link: {title}")
                                    skip_this = True
                                    break
                            
                            if skip_this:
                                continue
                            
                            # Only include actual album links
                            if href and ('/album/' in href or ('/POLeNo/' in href and '?' in href and 'secret=' in href)):
                                # Additional check: skip if it's the same URL as current page (navigation)
                                current_url = self.driver.current_url
                                if href != current_url and not href.endswith('/57347') and not href.endswith('/57348'):
                                    albums.append({
                                        'url': href,
                                        'title': title or f"Album_{len(albums)+1}"
                                    })
                                    print(f"Found album: {title} - {href}")
                        if albums:  # If we found albums with this selector, use them
                            break
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue
            
            if not albums:
                print("No photo albums found with standard selectors. Let's try to find any links...")
                # Fallback: get all links and filter manually
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"Found {len(all_links)} total links on page")
                
                relevant_links = []
                for link in all_links:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if href and text and not any(skip.lower() in text.lower() for skip in skip_patterns):
                        relevant_links.append(f"Link: {text} -> {href}")
                
                # Show only first 20 relevant links to avoid spam
                for link_info in relevant_links[:20]:
                    print(link_info)
                
                if len(relevant_links) > 20:
                    print(f"... and {len(relevant_links) - 20} more links")
                
                return []
            
            print(f"Found {len(albums)} actual photo albums")
            return albums
            
        except Exception as e:
            print(f"Error getting album links: {e}")
            return []
    
    def get_album_title_from_page(self):
        """Extract album title from the current page"""
        try:
            # Try different selectors for album title
            title_selectors = [
                "h1",  # Main heading
                ".album-title",
                "#album-title", 
                "[data-testid='album-title']",
                "h2",
                "h3",
                ".title",
                ".album-name"
            ]
            
            for selector in title_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        title = element.text.strip()
                        if title and len(title) > 2:  # Valid title
                            print(f"Found album title: '{title}' using selector: {selector}")
                            return title
                except Exception as e:
                    continue
            
            # Fallback: try to get title from page title
            page_title = self.driver.title
            if page_title and "zonerama" not in page_title.lower():
                print(f"Using page title as album name: '{page_title}'")
                return page_title
                
            return None
            
        except Exception as e:
            print(f"Error getting album title: {e}")
            return None
    
    def is_album_already_downloaded(self, album_title):
        """Check if album is already downloaded by looking for ZIP file"""
        try:
            if not album_title:
                return False
            
            # Remove diacritics from album title to match filesystem naming
            album_title_no_diacritics = self.remove_diacritics(album_title)
            
            # Clean the album title for filename use (this is what the browser/system would do)
            import re
            
            # Apply the same cleaning logic that would be applied when downloading
            def clean_for_filename(text):
                # Replace invalid filename characters with underscore
                cleaned = re.sub(r'[<>:"/\\|?*&]', '_', text)
                return cleaned.strip()
            
            # Try various combinations to match how the file might be named
            potential_names = [
                clean_for_filename(album_title_no_diacritics),  # Most likely: no diacritics + cleaned
                clean_for_filename(album_title),  # Original + cleaned
                album_title_no_diacritics,  # No diacritics, no cleaning
                album_title,  # Original, no changes
            ]
            
            # Remove duplicates while preserving order  
            seen = set()
            unique_names = []
            for name in potential_names:
                if name and name not in seen:
                    seen.add(name)
                    unique_names.append(name)
            
            # Check for ZIP files with these names
            for name in unique_names:
                filename = f"{name}.zip"
                zip_path = os.path.join(self.download_dir, filename)
                if os.path.exists(zip_path):
                    file_size = os.path.getsize(zip_path)
                    if file_size > 1024:  # At least 1KB - not empty
                        print(f"✅ Album already downloaded: {filename} ({file_size} bytes)")
                        print(f"   Original title: '{album_title}'")
                        print(f"   Matched as: '{name}'")
                        return True
                    else:
                        print(f"⚠️  Found but empty/small file: {filename} - will re-download")
            
            return False
            
        except Exception as e:
            print(f"Error checking for existing album: {e}")
            return False

    def download_album(self, album_url, album_title):
        """Download a single album"""
        try:
            print(f"Processing album: {album_title}")
            self.driver.get(album_url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Get the actual album title from the page
            actual_title = self.get_album_title_from_page()
            if actual_title:
                album_title = actual_title
                print(f"Updated album title from page: {album_title}")
            
            # Check if album is already downloaded
            if self.is_album_already_downloaded(album_title):
                print(f"⏭️  SKIPPING: Album '{album_title}' is already downloaded")
                return True  # Consider this a success since we don't need to download again
            
            # Look for the specific download button first
            download_selectors = [
                "#header-album-download",  # Specific ID from your example
                "a[data-target='#dialog-download']",  # Modal trigger
                "a.share-a[data-ajax-url*='DownloadAlbum']",  # By class and URL pattern
                "//a[contains(@data-ajax-url, 'DownloadAlbum')]",  # XPath version
                "//button[contains(text(), 'Stáhnout')]",  # Czech version fallback
                "//a[contains(text(), 'Stáhnout')]",
                "//button[contains(text(), 'Download')]",
                "//a[contains(text(), 'Download')]",
                "[data-testid='download-button']",
                ".download-btn",
                ".download-button"
            ]
            
            download_clicked = False
            for selector in download_selectors:
                try:
                    print(f"Trying selector: {selector}")
                    if selector.startswith("//"):
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        element = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    print(f"Found download element with selector: {selector}")
                    self.driver.execute_script("arguments[0].click();", element)
                    print(f"Clicked download button for: {album_title}")
                    
                    # Wait for modal to appear and fully load
                    time.sleep(2)
                    
                    # Wait for modal to be visible
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "#dialog-download"))
                        )
                        print("Modal is now visible")
                    except:
                        print("Modal did not appear")
                        continue
                    
                    # Enable original photos option
                    switch_clicked = False
                    try:
                        print("Looking for original photos checkbox...")
                        # First check if the checkbox is already checked
                        checkbox = self.driver.find_element(By.CSS_SELECTOR, "#dialog-download-org")
                        
                        if not checkbox.is_selected():
                            print("Original photos option is OFF, enabling it...")
                            # Find the associated switchery element and click it
                            switchery_elements = self.driver.find_elements(By.CSS_SELECTOR, "#dialog-download .switchery")
                            
                            for switchery in switchery_elements:
                                classes = switchery.get_attribute('class')
                                print(f"Found switchery with classes: {classes}")
                                
                                # If this switchery doesn't have 'switchery-on', click it
                                if 'switchery-on' not in classes:
                                    print("Clicking switchery to enable original photos")
                                    self.driver.execute_script("arguments[0].click();", switchery)
                                    time.sleep(1)  # Wait for animation
                                    
                                    # Verify the checkbox is now checked
                                    if checkbox.is_selected():
                                        print("Original photos option successfully enabled")
                                        switch_clicked = True
                                        break
                                    else:
                                        print("Checkbox still not checked, trying next switchery")
                                else:
                                    print("This switchery is already ON")
                        else:
                            print("Original photos option is already enabled")
                            switch_clicked = True
                            
                    except Exception as switch_e:
                        print(f"Error enabling original photos option: {switch_e}")
                        # Fallback: try clicking the checkbox directly
                        try:
                            print("Trying to click checkbox directly...")
                            checkbox = self.driver.find_element(By.CSS_SELECTOR, "#dialog-download-org")
                            if not checkbox.is_selected():
                                self.driver.execute_script("arguments[0].click();", checkbox)
                                switch_clicked = True
                                print("Checkbox clicked directly")
                            else:
                                switch_clicked = True
                                print("Checkbox already selected")
                        except Exception as checkbox_e:
                            print(f"Direct checkbox click failed: {checkbox_e}")
                    
                    # Wait a moment after enabling the option
                    time.sleep(1)
                    
                    # Now click the download button in the modal
                    try:
                        print("Looking for download button in modal...")
                        download_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "#dialog-download-submit"))
                        )
                        
                        print("Found download button, clicking...")
                        self.driver.execute_script("arguments[0].click();", download_button)
                        print(f"Clicked download button for: {album_title}")
                        
                        # Wait for modal to close (indicating download preparation is complete)
                        print("Waiting for modal to close (download preparation)...")
                        try:
                            WebDriverWait(self.driver, 60).until(
                                EC.invisibility_of_element_located((By.CSS_SELECTOR, "#dialog-download"))
                            )
                            print("Modal closed - download preparation complete")
                        except:
                            print("Modal did not close within 60 seconds, but continuing...")
                        
                        download_clicked = True
                        break
                        
                    except Exception as download_e:
                        print(f"Error clicking download button: {download_e}")
                        
                        # Fallback: try alternative selectors
                        fallback_selectors = [
                            "//button[contains(text(), 'Stáhnout') and not(contains(text(), 'originály'))]",
                            "#dialog-download button.btn-success",
                            "#dialog-download .btn-primary"
                        ]
                        
                        modal_clicked = False
                        for fallback_selector in fallback_selectors:
                            try:
                                print(f"Trying fallback selector: {fallback_selector}")
                                if fallback_selector.startswith("//"):
                                    modal_element = WebDriverWait(self.driver, 3).until(
                                        EC.element_to_be_clickable((By.XPATH, fallback_selector))
                                    )
                                else:
                                    modal_element = WebDriverWait(self.driver, 3).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, fallback_selector))
                                    )
                                
                                print(f"Found fallback download button")
                                self.driver.execute_script("arguments[0].click();", modal_element)
                                print(f"Clicked fallback download button for: {album_title}")
                                
                                # Wait for modal to close
                                try:
                                    WebDriverWait(self.driver, 60).until(
                                        EC.invisibility_of_element_located((By.CSS_SELECTOR, "#dialog-download"))
                                    )
                                    print("Modal closed - download preparation complete")
                                except:
                                    print("Modal did not close within 60 seconds")
                                
                                modal_clicked = True
                                download_clicked = True
                                break
                                
                            except Exception as fallback_e:
                                print(f"Fallback selector {fallback_selector} failed: {fallback_e}")
                                continue
                        
                        if modal_clicked:
                            break
                    
                except Exception as e:
                    print(f"Selector {selector} failed: {e}")
                    continue
            
            if not download_clicked:
                print(f"Could not find download button for: {album_title}")
                # Let's see what buttons/links are available
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                links = self.driver.find_elements(By.TAG_NAME, "a")
                spans = self.driver.find_elements(By.CSS_SELECTOR, "span.switchery")
                
                print("Available buttons:")
                for btn in buttons[:10]:
                    text = btn.text.strip()
                    btn_id = btn.get_attribute('id')
                    btn_class = btn.get_attribute('class')
                    if text or btn_id:
                        print(f"  - {text} (id: {btn_id}, class: {btn_class})")
                
                print("Available links:")
                for link in links[:10]:
                    text = link.text.strip()
                    href = link.get_attribute('href')
                    link_id = link.get_attribute('id')
                    link_class = link.get_attribute('class')
                    if text and href:
                        print(f"  - {text} -> {href} (id: {link_id}, class: {link_class})")
                
                print("Available switchery elements:")
                for span in spans:
                    span_class = span.get_attribute('class')
                    print(f"  - Switchery: class={span_class}")
                
                return False
            
            # Additional wait for download to fully start
            print("Waiting for download to start...")
            time.sleep(5)
            return True
            
        except Exception as e:
            print(f"Error downloading album {album_title}: {e}")
            return False
    
    def unzip_all_albums(self, delete_zips=False):
        """Unzip all ZIP files in the download directory
        
        Args:
            delete_zips (bool): If True, delete ZIP files after successful extraction
        """
        try:
            print("\n" + "=" * 60)
            print("📦 UNZIPPING DOWNLOADED ALBUMS")
            print("=" * 60)
            
            # Find all ZIP files in download directory
            zip_files = []
            for file in os.listdir(self.download_dir):
                if file.lower().endswith('.zip'):
                    zip_path = os.path.join(self.download_dir, file)
                    if os.path.getsize(zip_path) > 1024:  # At least 1KB
                        zip_files.append(zip_path)
            
            if not zip_files:
                print("📭 No ZIP files found to unzip.")
                return True
            
            print(f"📥 Found {len(zip_files)} ZIP files to unzip:")
            for zip_file in zip_files:
                print(f"   - {os.path.basename(zip_file)}")
            
            if delete_zips:
                print("🗑️  ZIP files will be deleted after successful extraction")
            
            print("\n🔄 Starting unzip process...")
            
            successful_unzips = 0
            failed_unzips = 0
            deleted_zips = 0
            
            for zip_path in zip_files:
                zip_filename = os.path.basename(zip_path)
                album_name = os.path.splitext(zip_filename)[0]  # Remove .zip extension
                
                # Create directory for this album
                album_dir = os.path.join(self.download_dir, album_name)
                
                # Check if already unzipped
                if os.path.exists(album_dir) and os.listdir(album_dir):
                    print(f"⏭️  SKIPPING: {album_name} (already unzipped)")
                    
                    # If delete is requested and this was already unzipped, offer to delete the ZIP
                    if delete_zips:
                        try:
                            os.remove(zip_path)
                            print(f"   🗑️  DELETED: {zip_filename} (album was already unzipped)")
                            deleted_zips += 1
                        except Exception as del_e:
                            print(f"   ⚠️  Could not delete {zip_filename}: {del_e}")
                    continue
                
                try:
                    print(f"📂 Unzipping: {zip_filename}")
                    
                    # Create album directory
                    os.makedirs(album_dir, exist_ok=True)
                    
                    # Unzip the file
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(album_dir)
                    
                    # Count extracted files
                    extracted_files = []
                    for root, dirs, files in os.walk(album_dir):
                        extracted_files.extend(files)
                    
                    print(f"   ✅ SUCCESS: Extracted {len(extracted_files)} files to {album_name}/")
                    successful_unzips += 1
                    
                    # Delete ZIP file if requested and extraction was successful
                    if delete_zips:
                        try:
                            os.remove(zip_path)
                            print(f"   🗑️  DELETED: {zip_filename}")
                            deleted_zips += 1
                        except Exception as del_e:
                            print(f"   ⚠️  Could not delete {zip_filename}: {del_e}")
                    
                except zipfile.BadZipFile as e:
                    print(f"   ❌ ERROR: {zip_filename} is corrupted or not a valid ZIP file")
                    failed_unzips += 1
                except Exception as e:
                    print(f"   ❌ ERROR: Failed to unzip {zip_filename}: {e}")
                    failed_unzips += 1
            
            print("\n" + "=" * 60)
            print("📊 UNZIP SUMMARY")
            print("=" * 60)
            print(f"✅ Successfully unzipped: {successful_unzips}")
            print(f"❌ Failed to unzip: {failed_unzips}")
            if delete_zips:
                print(f"🗑️  ZIP files deleted: {deleted_zips}")
            print(f"📁 Files location: {os.path.abspath(self.download_dir)}")
            print("=" * 60)
            
            return failed_unzips == 0
            
        except Exception as e:
            print(f"❌ Error during unzip process: {e}")
            return False

    def run(self, unzip_albums=False, delete_zips=False):
        """Main execution method
        
        Args:
            unzip_albums (bool): Whether to unzip albums after download
            delete_zips (bool): Whether to delete ZIP files after successful unzip
        """
        try:
            # Setup driver
            self.setup_driver()
            
            # Wait for manual login
            if not self.wait_for_login():
                return False
            
            # Navigate to hidden albums
            if not self.navigate_to_hidden_albums():
                return False
            
            # Get all album links
            albums = self.get_album_links()
            if not albums:
                print("No albums found. Check the page manually.")
                input("Press Enter to continue anyway (browser will stay open)...")
                return False
            
            # Download each album
            successful_downloads = 0
            for i, album in enumerate(albums, 1):
                print(f"\nProcessing album {i}/{len(albums)}: {album['title']}")
                if self.download_album(album['url'], album['title']):
                    successful_downloads += 1
                
                # Small delay between downloads
                time.sleep(2)
            
            print(f"\nDownload completed! Successfully initiated {successful_downloads}/{len(albums)} downloads")
            print(f"Files should be downloaded to: {os.path.abspath(self.download_dir)}")
            
        except Exception as e:
            print(f"Error during execution: {e}")
        finally:
            if self.driver:
                print("\n" + "=" * 60)
                print("🔽 DOWNLOAD PROCESS COMPLETED")
                print("=" * 60)
                print("⚠️  IMPORTANT: The browser will remain open to ensure downloads complete properly.")
                print("📥 Downloads may still be in progress in the background.")
                print("🔍 You can monitor the download progress in your browser's download manager.")
                print("💾 Files are being downloaded to:", os.path.abspath(self.download_dir))
                print("=" * 60)
                print("🚫 DO NOT CLOSE THE BROWSER until all downloads are finished!")
                print("   When ready, close the browser manually or press Ctrl+C here.")
                print("=" * 60)
                
                try:
                    # Keep the script running and browser open
                    input("Press Enter when all downloads are complete to close the browser" + 
                          (" and unzip albums..." if unzip_albums else "..."))
                    print("Closing browser...")
                    self.driver.quit()
                    print("✅ Browser closed successfully.")
                    
                    # Unzip albums if requested
                    if unzip_albums:
                        print("\n⏳ Processing downloaded albums...")
                        self.unzip_all_albums(delete_zips=delete_zips)
                    else:
                        print("📦 Unzipping skipped (use -u to enable auto-unzip)")
                    
                except KeyboardInterrupt:
                    print("\n🛑 Interrupted by user. Closing browser...")
                    self.driver.quit()
                    print("✅ Browser closed.")
                    
                    # Ask if user wants to unzip anyway
                    if unzip_albums:
                        try:
                            response = input("Would you like to unzip downloaded albums? (y/n): ")
                            if response.lower().startswith('y'):
                                self.unzip_all_albums(delete_zips=delete_zips)
                        except KeyboardInterrupt:
                            print("\n🛑 Skipping unzip process.")
                            
                except Exception as close_e:
                    print(f"Error closing browser: {close_e}")
                    print("Please close the browser manually.")
                    
                    # Still try to unzip if requested
                    if unzip_albums:
                        try:
                            response = input("Would you like to unzip downloaded albums? (y/n): ")
                            if response.lower().startswith('y'):
                                self.unzip_all_albums(delete_zips=delete_zips)
                        except:
                            print("Skipping unzip process.")

def main():
    """Main function with argument parsing"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Expand user home directory if needed
    download_dir = os.path.expanduser(args.download_dir)
    
    # Display configuration
    print("=" * 60)
    print("🔽 Zonerama Album Downloader")
    print("=" * 60)
    print(f"📁 Download directory: {os.path.abspath(download_dir)}")
    
    if args.unzip:
        if args.delete:
            print("📦 Auto-unzip: ✅ ENABLED (with ZIP deletion)")
        else:
            print("📦 Auto-unzip: ✅ ENABLED")
    else:
        print("📦 Auto-unzip: ❌ DISABLED (use -u to enable)")
    
    print("=" * 60)
    
    # Create and run downloader
    downloader = ZoneramaDownloader(download_dir=download_dir)
    downloader.run(unzip_albums=args.unzip, delete_zips=args.delete)

if __name__ == "__main__":
    main()