"""
Zonerama Downloader - A tool for downloading albums from Zonerama.com

This package provides a modular approach to downloading photo albums
from Zonerama.com using Selenium WebDriver automation.
"""

__version__ = "1.0.0"
__author__ = "Zonerama Downloader"
__description__ = "Download photo albums from Zonerama.com"

# Main exports
from .config import Config
from .downloader import ZoneramaDownloader
from .cli import parse_arguments
from .scraper import ZoneramaScraper
from . import file_utils
