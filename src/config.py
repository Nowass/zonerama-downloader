"""
Configuration module for Zonerama Downloader

Handles application configuration and constants
"""

import os


class Config:
    """Configuration class for the Zonerama Downloader"""
    
    # Application info
    APP_NAME = "Zonerama Album Downloader"
    VERSION = "1.0.0"
    DESCRIPTION = "Download albums from Zonerama.com"
    
    # Default settings
    DEFAULT_DOWNLOAD_DIR = "downloads"
    MIN_ZIP_SIZE = 1024  # Minimum ZIP file size in bytes (1KB)
    
    # Zonerama URLs
    BASE_URL = "https://eu.zonerama.com/"
    LOGIN_URL = "https://eu.zonerama.com/"
    PUBLIC_ALBUMS_URL = "https://eu.zonerama.com/POLeNo/57347"
    HIDDEN_ALBUMS_URL = "https://eu.zonerama.com/POLeNo/57348?secret=2D2359641FEE4833A68BD152F809DF1E"
    ALBUMS_URL = "https://eu.zonerama.com/POLeNo/57348?secret=2D2359641FEE4833A68BD152F809DF1E"  # Backwards compatibility
    
    # Timeouts and delays (in seconds)
    timeout_default = 10          # Default WebDriver wait timeout
    timeout_download = 300        # Download completion timeout (5 minutes)
    PAGE_LOAD_DELAY = 3
    MODAL_WAIT_TIMEOUT = 10
    DOWNLOAD_WAIT_TIMEOUT = 60
    BETWEEN_DOWNLOADS_DELAY = 2
    DOWNLOAD_START_DELAY = 5
    
    # Web scraping selectors
    COOKIE_ACCEPT_SELECTOR = "button[data-action='accept-all']"
    ALBUM_SELECTOR = "a[href*='/album/']"  # Single selector for backwards compatibility
    ALBUM_NAME_SELECTOR = "h3, .album-title, [data-testid='album-title']"
    DOWNLOAD_BUTTON_SELECTOR = "#header-album-download, a[data-target='#dialog-download']"
    MODAL_DOWNLOAD_SELECTOR = "#dialog-download-submit, #dialog-download .btn-primary"
    
    # Album selectors array (used by scraper)
    ALBUM_SELECTORS = [
        "a[href*='/album/']",
        "a[href*='/POLeNo/']",
        ".album-link",
        ".album-item a",
        "[data-testid='album-link']",
        "a[title]"  # Generic link with title
    ]
    
    # Selectors for web scraping (legacy arrays - kept for compatibility)
    DOWNLOAD_SELECTORS = [
        "#header-album-download",
        "a[data-target='#dialog-download']",
        "a.share-a[data-ajax-url*='DownloadAlbum']",
        "//a[contains(@data-ajax-url, 'DownloadAlbum')]",
        "//button[contains(text(), 'Stáhnout')]",
        "//a[contains(text(), 'Stáhnout')]",
        "//button[contains(text(), 'Download')]",
        "//a[contains(text(), 'Download')]",
        "[data-testid='download-button']",
        ".download-btn",
        ".download-button"
    ]
    
    TITLE_SELECTORS = [
        "h1",
        ".album-title",
        "#album-title",
        "[data-testid='album-title']",
        "h2",
        "h3",
        ".title",
        ".album-name"
    ]
    
    FALLBACK_DOWNLOAD_SELECTORS = [
        "//button[contains(text(), 'Stáhnout') and not(contains(text(), 'originály'))]",
        "#dialog-download button.btn-success",
        "#dialog-download .btn-primary"
    ]
    
    # Skip patterns for navigation links
    SKIP_PATTERNS = [
        'Veřejná alba',
        'Skrytá alba',
        'Public albums',
        'Hidden albums',
        'inzerce',
        'advertisement'
    ]
    
    # Modal selectors
    MODAL_SELECTOR = "#dialog-download"
    MODAL_CHECKBOX_SELECTOR = "#dialog-download-org"
    MODAL_SWITCHERY_SELECTOR = "#dialog-download .switchery"
    MODAL_SUBMIT_SELECTOR = "#dialog-download-submit"
    
    def __init__(self, download_dir=None, unzip=False, delete_zips=False):
        """Initialize configuration
        
        Args:
            download_dir (str): Download directory path
            unzip (bool): Whether to unzip downloaded albums
            delete_zips (bool): Whether to delete ZIP files after unzipping
        """
        self.download_dir = download_dir or self.DEFAULT_DOWNLOAD_DIR
        self.download_dir = os.path.expanduser(self.download_dir)
        self.unzip = unzip
        self.delete_zips = delete_zips
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
    
    @property
    def absolute_download_dir(self):
        """Get absolute path of download directory"""
        return os.path.abspath(self.download_dir)
