import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin, urlparse
import zipfile
import tempfile

class ZoneramaDownloader:
    def __init__(self, download_dir="downloads"):
        self.download_dir = download_dir
        self.driver = None
        self.session = requests.Session()
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
        
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
    
    def download_album(self, album_url, album_title):
        """Download a single album"""
        try:
            print(f"Processing album: {album_title}")
            self.driver.get(album_url)
            
            # Wait for page to load
            time.sleep(3)
            
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
                    time.sleep(3)
                    
                    # Wait for modal to be visible
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "#dialog-download, .modal"))
                        )
                        print("Modal is now visible")
                    except:
                        print("Modal did not appear")
                        continue
                    
                    # Look for the switchery toggle for original photos
                    switch_clicked = False
                    switch_selectors = [
                        ".switchery",  # The switchery component
                        "span.switchery",
                        ".switchery-default",
                        "//span[contains(@class, 'switchery')]",
                        "#dialog-download .switchery",
                        ".modal .switchery"
                    ]
                    
                    for switch_selector in switch_selectors:
                        try:
                            print(f"Looking for switchery toggle with: {switch_selector}")
                            if switch_selector.startswith("//"):
                                switch_element = WebDriverWait(self.driver, 3).until(
                                    EC.element_to_be_clickable((By.XPATH, switch_selector))
                                )
                            else:
                                switch_element = WebDriverWait(self.driver, 3).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, switch_selector))
                                )
                            
                            # Check if switch is already on (has switchery-on class)
                            switch_classes = switch_element.get_attribute('class')
                            print(f"Switch classes: {switch_classes}")
                            
                            if 'switchery-on' not in switch_classes:
                                print("Switch is OFF, clicking to turn ON")
                                self.driver.execute_script("arguments[0].click();", switch_element)
                                time.sleep(1)  # Wait for animation
                                print("Clicked switchery toggle for original photos")
                            else:
                                print("Switch is already ON")
                            
                            switch_clicked = True
                            break
                            
                        except Exception as switch_e:
                            print(f"Switch selector {switch_selector} failed: {switch_e}")
                            continue
                    
                    # Fallback: try to find and click regular checkbox if switchery failed
                    if not switch_clicked:
                        print("Switchery toggle failed, trying regular checkbox")
                        checkbox_selectors = [
                            "//label[contains(text(), 'Stáhnout originály fotek')]//input[@type='checkbox']",
                            "//label[contains(text(), 'originály')]//input[@type='checkbox']",
                            "#dialog-download input[type='checkbox']",
                            ".modal input[type='checkbox']",
                            "input[type='checkbox'][name*='original']",
                            "input[type='checkbox'][id*='original']"
                        ]
                        
                        for checkbox_selector in checkbox_selectors:
                            try:
                                print(f"Looking for checkbox with: {checkbox_selector}")
                                if checkbox_selector.startswith("//"):
                                    checkbox = WebDriverWait(self.driver, 3).until(
                                        EC.element_to_be_clickable((By.XPATH, checkbox_selector))
                                    )
                                else:
                                    checkbox = WebDriverWait(self.driver, 3).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, checkbox_selector))
                                    )
                                
                                if not checkbox.is_selected():
                                    print("Checking checkbox for original photos")
                                    self.driver.execute_script("arguments[0].click();", checkbox)
                                    switch_clicked = True
                                    print("Checkbox checked successfully")
                                else:
                                    print("Checkbox already checked")
                                    switch_clicked = True
                                break
                            except Exception as checkbox_e:
                                print(f"Checkbox selector {checkbox_selector} failed: {checkbox_e}")
                                continue
                    
                    # Wait a moment after toggling the switch/checkbox
                    time.sleep(2)
                    
                    # Now look for the download button in the modal
                    modal_download_selectors = [
                        "//button[contains(text(), 'Stáhnout') and not(contains(text(), 'originály'))]",
                        "//a[contains(text(), 'Stáhnout') and not(contains(text(), 'originály'))]",
                        "//button[contains(text(), 'Download')]",
                        "//a[contains(text(), 'Download')]",
                        "#dialog-download button.btn-success",
                        "#dialog-download .btn-primary",
                        ".modal button.btn-success",
                        ".modal .btn-primary",
                        "#dialog-download button[type='submit']",
                        ".modal button[type='submit']",
                        "#dialog-download button",
                        ".modal-footer button"
                    ]
                    
                    modal_clicked = False
                    for modal_selector in modal_download_selectors:
                        try:
                            print(f"Looking for modal download button with: {modal_selector}")
                            if modal_selector.startswith("//"):
                                modal_element = WebDriverWait(self.driver, 3).until(
                                    EC.element_to_be_clickable((By.XPATH, modal_selector))
                                )
                            else:
                                modal_element = WebDriverWait(self.driver, 3).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, modal_selector))
                                )
                            
                            print(f"Found modal download element: {modal_selector}")
                            self.driver.execute_script("arguments[0].click();", modal_element)
                            print(f"Clicked modal download for: {album_title}")
                            modal_clicked = True
                            break
                        except Exception as modal_e:
                            print(f"Modal selector {modal_selector} failed: {modal_e}")
                            continue
                    
                    if modal_clicked:
                        # Wait for modal to close (indicating download preparation is complete)
                        print("Waiting for modal to close (download preparation)...")
                        try:
                            WebDriverWait(self.driver, 60).until(
                                EC.invisibility_of_element_located((By.CSS_SELECTOR, "#dialog-download, .modal"))
                            )
                            print("Modal closed - download preparation complete")
                        except:
                            print("Modal did not close within 60 seconds, but continuing...")
                        
                        download_clicked = True
                        break
                    else:
                        print("Modal opened but couldn't find download button inside")
                        # Let's see what's in the modal
                        try:
                            modal_content = self.driver.find_element(By.CSS_SELECTOR, "#dialog-download, .modal")
                            print("Modal content:")
                            modal_links = modal_content.find_elements(By.TAG_NAME, "a")
                            modal_buttons = modal_content.find_elements(By.TAG_NAME, "button")
                            modal_spans = modal_content.find_elements(By.TAG_NAME, "span")
                            
                            for link in modal_links:
                                text = link.text.strip()
                                href = link.get_attribute('href')
                                if text or href:
                                    print(f"  Modal link: {text} -> {href}")
                            
                            for btn in modal_buttons:
                                text = btn.text.strip()
                                btn_type = btn.get_attribute('type')
                                btn_class = btn.get_attribute('class')
                                if text:
                                    print(f"  Modal button: {text} (type: {btn_type}, class: {btn_class})")
                            
                            for span in modal_spans:
                                span_class = span.get_attribute('class')
                                if 'switchery' in span_class:
                                    print(f"  Modal span (switchery): class={span_class}")
                        except:
                            print("Could not inspect modal content")
                        
                        # Try clicking any visible download-related element
                        try:
                            all_modal_elements = self.driver.find_elements(By.CSS_SELECTOR, "#dialog-download *, .modal *")
                            for elem in all_modal_elements:
                                text = elem.text.strip().lower()
                                if text == 'stáhnout' and 'originály' not in text:
                                    print(f"Trying to click download button: {text}")
                                    self.driver.execute_script("arguments[0].click();", elem)
                                    modal_clicked = True
                                    download_clicked = True
                                    
                                    # Wait for modal to close
                                    print("Waiting for modal to close...")
                                    try:
                                        WebDriverWait(self.driver, 60).until(
                                            EC.invisibility_of_element_located((By.CSS_SELECTOR, "#dialog-download, .modal"))
                                        )
                                        print("Modal closed - download preparation complete")
                                    except:
                                        print("Modal did not close within 60 seconds")
                                    break
                        except:
                            pass
                        
                        if download_clicked:
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
    
    def run(self):
        """Main execution method"""
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
                print("Keeping browser open for manual verification. Close it manually when done.")
                # Don't auto-close to allow user to see download progress
                # self.driver.quit()

def main():
    downloader = ZoneramaDownloader()
    downloader.run()

if __name__ == "__main__":
    main()