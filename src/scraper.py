"""
Web scraping utilities for Zonerama Downloader

Handles Selenium WebDriver interactions and web page processing
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementClickInterceptedException,
    StaleElementReferenceException, WebDriverException
)

from .config import Config


class ZoneramaScraper:
    """Handles web scraping interactions with Zonerama.com"""
    
    def __init__(self, config):
        """Initialize the scraper with configuration
        
        Args:
            config (Config): Configuration object
        """
        self.config = config
        self.driver = None
        self.wait = None
    
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set download preferences
        prefs = {
            "download.default_directory": self.config.absolute_download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, self.config.timeout_default)
            return True
        except WebDriverException as e:
            print(f"❌ Error setting up Chrome WebDriver: {e}")
            return False
    
    def close_driver(self):
        """Close the WebDriver safely"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None
                self.wait = None
    
    def wait_for_login(self):
        """Open Zonerama and wait for user to login manually
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("🌐 Opening Zonerama login page...")
            self.driver.get(self.config.LOGIN_URL)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            print("👤 Please login manually in the browser window.")
            print("🔄 After logging in, press Enter in this terminal to continue...")
            
            # Wait for user confirmation that they've logged in
            input()
            
            print("✅ Proceeding with assumption that login was successful...")
            return True
            
        except TimeoutException:
            print("❌ Timeout loading Zonerama login page")
            return False
        except WebDriverException as e:
            print(f"❌ Error during login process: {e}")
            return False
    
    def navigate_to_hidden_albums(self):
        """Navigate to hidden albums section
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("📂 Navigating to hidden albums section...")
            self.driver.get(self.config.HIDDEN_ALBUMS_URL)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)  # Additional wait for dynamic content
            
            print("✅ Navigated to hidden albums section")
            return True
            
        except TimeoutException:
            print("❌ Timeout loading hidden albums page")
            return False
        except WebDriverException as e:
            print(f"❌ Error navigating to hidden albums: {e}")
            return False
    
    def navigate_to_albums(self):
        """Wait for manual login and then automatically handle album loading
        
        Returns:
            bool: True if successful, False otherwise
        """
        # First wait for manual login
        if not self.wait_for_login():
            return False
        
        # Now wait for user to manually navigate to the desired albums page
        print("📂 Please manually navigate to the albums page you want to download from:")
        print("   - For hidden albums: Click 'Skrytá alba'")
        print("   - For public albums: Click 'Veřejná alba'")
        print("   - Or stay on current page if already where you want to be")
        print("🔄 After navigating to the desired page, press Enter and the script will automatically scroll and wait for all albums to load...")
        
        try:
            input()  # Wait for user confirmation
            print("✅ Starting automatic album loading process...")
            
            # Wait a moment for any page transitions to complete
            time.sleep(2)
            
            return True
            
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return False

    def navigate_to_hidden_albums(self):
        """Navigate to hidden albums section (kept for compatibility but not used in manual mode)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("� Navigating to hidden albums section...")
            self.driver.get(self.config.HIDDEN_ALBUMS_URL)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)  # Additional wait for dynamic content
            
            print("✅ Navigated to hidden albums section")
            return True
            
        except TimeoutException:
            print("❌ Timeout loading hidden albums page")
            return False
        except WebDriverException as e:
            print(f"❌ Error navigating to hidden albums: {e}")
            return False

    def navigate_to_public_albums(self):
        """Navigate to public albums section
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("📂 Navigating to public albums section...")
            self.driver.get(self.config.PUBLIC_ALBUMS_URL)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)  # Additional wait for dynamic content
            
            print("✅ Navigated to public albums section")
            return True
            
        except TimeoutException:
            print("❌ Timeout loading public albums page")
            return False
        except WebDriverException as e:
            print(f"❌ Error navigating to public albums: {e}")
            return False
    
    def handle_cookie_modal(self):
        """Handle cookie consent modal if it appears
        
        Returns:
            bool: True if handled or not present, False if error
        """
        try:
            # Look for cookie modal
            cookie_button = self.driver.find_element(
                By.CSS_SELECTOR, 
                self.config.COOKIE_ACCEPT_SELECTOR
            )
            if cookie_button.is_displayed():
                print("🍪 Accepting cookies...")
                cookie_button.click()
                time.sleep(1)
                return True
        except NoSuchElementException:
            # No cookie modal found, which is fine
            pass
        except Exception as e:
            print(f"⚠️  Warning: Could not handle cookie modal: {e}")
        
        return True
    
    def find_album_elements(self):
        """Find all album elements on the page and extract their data
        Simulates manual scrolling and waiting for all albums to load
        
        Returns:
            list: List of dictionaries with album data {'href': str, 'title': str}
        """
        try:
            print("🔄 Waiting for initial page load...")
            time.sleep(3)
            
            print("📜 Fast scrolling to trigger all album loading...")
            
            # Your optimized approach: Fast scrolling without checking
            print("🚀 Phase 1: Fast aggressive scrolling down...")
            for i in range(10):  # Fast scroll attempts
                scroll_position = (i + 1) * 1000  # Large scroll steps (1000px)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(0.5)  # Very short wait - just to let page catch up
            
            # Scroll to absolute bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for any final loading
            
            print("🔝 Phase 2: Scrolling back to top...")
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Optional: Repeat the process once more for thoroughness
            print("🔄 Phase 3: One more scroll cycle for thoroughness...")
            for i in range(5):  # Fewer, faster scrolls
                scroll_position = (i + 1) * 1500  # Even larger steps
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(0.3)  # Even shorter wait
            
            # Final bottom scroll
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Final top scroll (the magic step!)
            print("🎯 Phase 4: Final scroll to top for element collection...")
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(3)  # Slightly longer wait for DOM to stabilize
            
            print("🔍 Now collecting all album data...")
            
            # Use the album selectors array from config
            album_selectors = self.config.ALBUM_SELECTORS
            
            albums = []
            
            for selector in album_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"📂 Found {len(elements)} elements with selector: {selector}")
                        
                        for element in elements:
                            try:
                                href = element.get_attribute('href')
                                title = element.get_attribute('title') or element.text.strip()
                                
                                # Skip navigation links (same logic as original)
                                skip_this = False
                                for skip_pattern in self.config.SKIP_PATTERNS:
                                    if skip_pattern.lower() in title.lower():
                                        print(f"🚫 Skipping navigation link: {title}")
                                        skip_this = True
                                        break
                                
                                if skip_this:
                                    continue
                                
                                # Only include actual album links (same logic as original)
                                if href and ('/album/' in href or ('/POLeNo/' in href and '?' in href and 'secret=' in href)):
                                    # Additional check: skip if it's the same URL as current page (navigation)
                                    current_url = self.driver.current_url
                                    if (href != current_url and 
                                        not href.endswith('/57347') and 
                                        not href.endswith('/57348')):
                                        
                                        albums.append({
                                            'href': href,
                                            'title': title or f"Album_{len(albums) + 1}"
                                        })
                                        print(f"✅ Found album: {title} - {href}")
                                        
                            except Exception as e:
                                # Skip elements that cause errors (stale, etc.)
                                continue
                        
                        # CRITICAL: Break after first successful selector like original!
                        if albums:
                            print(f"✅ Using selector '{selector}' - found {len(albums)} albums")
                            break
                            
                except Exception as e:
                    print(f"⚠️  Error with selector '{selector}': {e}")
                    continue
            
            if not albums:
                print("⚠️  No photo albums found with standard selectors. Trying fallback...")
                # Fallback: get all links and filter manually (same as original)
                try:
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    print(f"🔍 Found {len(all_links)} total links on page")
                    
                    relevant_links = []
                    for link in all_links:
                        try:
                            href = link.get_attribute('href')
                            text = link.text.strip()
                            if href and text and not any(skip.lower() in text.lower() 
                                                        for skip in [s.lower() for s in self.config.SKIP_PATTERNS]):
                                relevant_links.append(f"Link: {text} -> {href}")
                        except Exception:
                            continue
                    
                    # Show only first 20 relevant links to avoid spam (same as original)
                    for link_info in relevant_links[:20]:
                        print(link_info)
                    
                    if len(relevant_links) > 20:
                        print(f"... and {len(relevant_links) - 20} more links")
                        
                except Exception as e:
                    print(f"⚠️  Error in fallback search: {e}")
            
            print(f"🎯 Final result: Found {len(albums)} albums total on the page")
            
            if len(albums) < 100:  # If we found suspiciously few albums
                print(f"⚠️  Only found {len(albums)} albums. Expected around 164.")
                print("💡 This might indicate the page hasn't fully loaded or uses different selectors.")
            
            return albums
            
        except Exception as e:
            print(f"❌ Error finding albums: {e}")
            return []
    
    def get_album_name(self, album_data):
        """Extract album name from album data
        
        Args:
            album_data (dict): Album data with 'href' and 'title' keys
            
        Returns:
            str: Album name
        """
        return album_data.get('title', 'Unknown Album')
    
    def navigate_to_album(self, album_url):
        """Navigate to an album by URL
        
        Args:
            album_url (str): URL of the album to navigate to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.driver.get(album_url)
            time.sleep(2)  # Wait for page to load
            return True
        except Exception as e:
            print(f"❌ Error navigating to album: {e}")
            return False
    
    def navigate_back(self):
        """Navigate back to albums list
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Navigate back to hidden albums page instead of using browser back
            self.driver.get(self.config.HIDDEN_ALBUMS_URL)
            time.sleep(3)  # Wait for page to load
            
            return True
            
        except Exception as e:
            print(f"❌ Error navigating back: {e}")
            return False
    
    def wait_for_download_button(self):
        """Wait for download button to be available and clickable
        
        Returns:
            WebElement or None: Download button element if found, None otherwise
        """
        try:
            download_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.config.DOWNLOAD_BUTTON_SELECTOR))
            )
            return download_button
        except TimeoutException:
            print("❌ Download button not found or not clickable")
            return None
    
    def click_download_button(self, download_button):
        """Click the download button
        
        Args:
            download_button: Selenium WebElement for download button
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Scroll to download button
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                download_button
            )
            time.sleep(1)
            
            download_button.click()
            return True
            
        except ElementClickInterceptedException:
            # Try JavaScript click
            try:
                self.driver.execute_script("arguments[0].click();", download_button)
                return True
            except Exception as e:
                print(f"❌ Could not click download button: {e}")
                return False
        except Exception as e:
            print(f"❌ Error clicking download button: {e}")
            return False
    
    def handle_download_modal(self):
        """Handle download modal that appears after clicking download
        Enables "original photos" option and then clicks download
        
        Returns:
            bool: True if handled successfully, False otherwise
        """
        try:
            # Wait for modal to appear and be visible
            print("⏳ Waiting for download modal to appear...")
            self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#dialog-download"))
            )
            print("📋 Download modal is now visible")
            time.sleep(2)  # Wait for modal to fully load
            
            # Enable original photos option
            switch_clicked = False
            try:
                print("🔍 Looking for original photos checkbox...")
                # First check if the checkbox is already checked
                checkbox = self.driver.find_element(By.CSS_SELECTOR, "#dialog-download-org")
                
                if not checkbox.is_selected():
                    print("📸 Original photos option is OFF, enabling it...")
                    # Find the associated switchery element and click it
                    switchery_elements = self.driver.find_elements(By.CSS_SELECTOR, "#dialog-download .switchery")
                    
                    for switchery in switchery_elements:
                        classes = switchery.get_attribute('class')
                        print(f"🔘 Found switchery with classes: {classes}")
                        
                        # If this switchery doesn't have 'switchery-on', click it
                        if 'switchery-on' not in classes:
                            print("🖱️  Clicking switchery to enable original photos")
                            self.driver.execute_script("arguments[0].click();", switchery)
                            time.sleep(1)  # Wait for animation
                            
                            # Verify the checkbox is now checked
                            if checkbox.is_selected():
                                print("✅ Original photos option successfully enabled")
                                switch_clicked = True
                                break
                            else:
                                print("⚠️  Checkbox still not checked, trying next switchery")
                        else:
                            print("✅ This switchery is already ON")
                            switch_clicked = True
                            break
                else:
                    print("✅ Original photos option is already enabled")
                    switch_clicked = True
                    
            except Exception as switch_e:
                print(f"⚠️  Error enabling original photos option: {switch_e}")
                # Fallback: try clicking the checkbox directly
                try:
                    print("🔄 Trying to click checkbox directly...")
                    checkbox = self.driver.find_element(By.CSS_SELECTOR, "#dialog-download-org")
                    if not checkbox.is_selected():
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        switch_clicked = True
                        print("✅ Checkbox clicked directly")
                    else:
                        switch_clicked = True
                        print("✅ Checkbox already selected")
                except Exception as checkbox_e:
                    print(f"❌ Direct checkbox click failed: {checkbox_e}")
            
            # Wait a moment after enabling the option
            time.sleep(1)
            
            # Now click the download button in the modal
            print("🔍 Looking for download button in modal...")
            modal_download_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#dialog-download-submit"))
            )
            
            print("💾 Clicking final download button in modal...")
            self.driver.execute_script("arguments[0].click();", modal_download_button)
            
            # Wait for modal to close (indicating download preparation is complete)
            print("⏳ Waiting for modal to close (download preparation)...")
            try:
                WebDriverWait(self.driver, 60).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "#dialog-download"))
                )
                print("✅ Modal closed - download preparation complete")
            except TimeoutException:
                print("⚠️  Modal did not close within 60 seconds, but continuing...")
            
            return True
            
        except TimeoutException:
            print("❌ Download modal did not appear or download button not found")
            return False
        except Exception as e:
            print(f"❌ Error handling download modal: {e}")
            return False
    
    def wait_for_download_completion(self, expected_filename_part, timeout=None):
        """Wait for download to complete by checking file system
        
        Args:
            expected_filename_part (str): Part of the expected filename
            timeout (int, optional): Timeout in seconds. Uses config default if None
            
        Returns:
            tuple: (success: bool, filepath: str or None)
        """
        if timeout is None:
            timeout = self.config.timeout_download
        
        import os
        from pathlib import Path
        
        download_dir = Path(self.config.absolute_download_dir)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Look for files containing the expected name part
                for file_path in download_dir.glob("*.zip"):
                    if expected_filename_part.lower() in file_path.name.lower():
                        # Check if file is completely downloaded (not .crdownload)
                        if not file_path.name.endswith('.crdownload'):
                            return True, str(file_path)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"⚠️  Warning: Error checking download: {e}")
                time.sleep(1)
        
        return False, None
    
    def is_page_responsive(self):
        """Check if the current page is responsive
        
        Returns:
            bool: True if page is responsive, False otherwise
        """
        try:
            # Try to execute a simple JavaScript command
            self.driver.execute_script("return document.readyState;")
            return True
        except Exception:
            return False
