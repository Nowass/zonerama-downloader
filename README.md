# Zonerama Downloader

A Python script to automatically download all albums from the "Skrytá alba" (Hidden Albums) section of Zonerama.com.

## Features

- Opens Zonerama in a browser and waits for manual login
- Automatically navigates to the hidden albums section
- Finds all available albums
- Downloads each album by clicking the download button
- Provides progress feedback during the process

## Prerequisites

- Python 3.6 or higher
- Google Chrome browser installed
- ChromeDriver (will be managed automatically by webdriver-manager)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/Nowass/zonerama-downloader.git
cd zonerama-downloader
```

2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the script with default settings (downloads to `./downloads` directory):

```bash
python3 zonerama-downloader.py
```

### Custom Download Directory

Specify a custom download directory:

```bash
python3 zonerama-downloader.py --download-dir ~/Downloads/Zonerama
# or short form:
python3 zonerama-downloader.py -d /path/to/your/downloads
```

### Command Line Options

```bash
python3 zonerama-downloader.py --help
```

Available options:
- `-d, --download-dir`: Specify download directory (default: `downloads`)
- `--version`: Show program version
- `-h, --help`: Show help message

### Download Process

1. The script will:

   - Display configuration (download directory)
   - Open a Chrome browser window with Zonerama.com
   - Wait for you to manually log in
   - Press Enter in the terminal once you're logged in
   - Automatically navigate to the hidden albums section (or ask you to navigate manually)
   - Find all albums and download them one by one

2. Downloaded files will be saved to your specified directory (defaults to `downloads` folder).

## How it works

The script uses Selenium WebDriver to:

1. Open a browser session to Zonerama
2. Wait for manual authentication (for security)
3. Navigate to the hidden albums section
4. Extract all album links from the page
5. Visit each album and click the download button
6. Monitor the download progress

## Troubleshooting

### ChromeDriver issues

If you encounter ChromeDriver issues, make sure you have Google Chrome installed and update to the latest version.

### Album not found

If the script can't find albums or download buttons, the website structure might have changed. You may need to:

- Navigate manually to the hidden albums section when prompted
- Check if the CSS selectors in the code need updating

### Download location

By default, files are downloaded to the `downloads` directory. You can change this by modifying the `download_dir` parameter when creating the `ZoneramaDownloader` instance.

## Customization

You can customize the download directory by modifying the script:

```python
downloader = ZoneramaDownloader(download_dir="my_custom_folder")
```

## Notes

- The script keeps the browser open after completion so you can monitor download progress
- Downloads are initiated by clicking the download buttons, actual download speed depends on your connection and Zonerama's servers
- The script handles both Czech and English versions of the Zonerama interface

## License

This project is for educational purposes. Please respect Zonerama's terms of service and only download content you own or have permission to download.
