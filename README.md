# Zonerama Downloader

A Python script to automatically download all albums from the "Skrytá alba" (Hidden Albums) section of Zonerama.com.

## Features

- Opens Zonerama in a browser and waits for manual login
- Automatically navigates to the hidden albums section
- Finds all available albums with duplicate detection
- Downloads each album by clicking the download button and enabling original photo quality
- Keeps browser open to ensure downloads complete properly
- Provides progress feedback during the process
- **Optional unzip functionality** - automatically extract downloaded albums
- **Smart cleanup** - optionally delete ZIP files after successful extraction
- **Configurable download directory** with flexible path support

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
- `-u, --unzip`: Automatically unzip downloaded albums after download completes
- `--delete`: Delete ZIP files after successful unzipping (requires `--unzip/-u`)
- `--version`: Show program version
- `-h, --help`: Show help message

### Advanced Usage Examples

```bash
# Download only (no automatic unzip)
python3 zonerama-downloader.py

# Download and automatically unzip albums
python3 zonerama-downloader.py -u

# Download, unzip, and delete ZIP files (saves space)
python3 zonerama-downloader.py -ud

# Custom directory with unzip and delete
python3 zonerama-downloader.py -d ~/Downloads/Zonerama -ud

# Long form (same as -ud)
python3 zonerama-downloader.py --download-dir ~/Photos --unzip --delete
```

### Path Support

The download directory supports various path formats:
- **Relative paths**: `./downloads`, `../backups`
- **Absolute paths**: `/home/user/Downloads`
- **Home directory expansion**: `~/Downloads/Zonerama`
- **Default fallback**: `downloads` directory

### Download Process

1. The script will:

   - Display configuration (download directory, unzip settings)
   - Open a Chrome browser window with Zonerama.com
   - Wait for you to manually log in
   - Press Enter in the terminal once you're logged in
   - Automatically navigate to the hidden albums section
   - Find all albums and check for duplicates (skips already downloaded)
   - Download new albums one by one
   - Keep browser open until you confirm downloads are complete
   - Optionally unzip albums and clean up ZIP files (if requested)

2. Downloaded files will be saved to your specified directory (defaults to `downloads` folder).

3. If unzip is enabled (`-u` or `-ud`), each album will be extracted to its own folder.

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

By default, files are downloaded to the `downloads` directory. You can change this using the `-d` or `--download-dir` option:

```bash
python3 zonerama-downloader.py -d ~/Downloads/Zonerama
```

### Unzip and cleanup options

- Use `-u` or `--unzip` to automatically extract downloaded albums
- Use `-ud` or `--unzip --delete` to extract and then delete ZIP files to save space
- The `--delete` option can only be used with `--unzip` for safety

## File Organization

When using the unzip feature, the script organizes files as follows:

```
downloads/
├── Album Name 1.zip          # Original ZIP (deleted if -ud used)
├── Album Name 1/             # Extracted folder
│   ├── photo1.jpg
│   ├── photo2.jpg
│   └── ...
├── Album Name 2.zip
├── Album Name 2/
│   └── ...
```

## Customization

The script provides several customization options via command line arguments:

```bash
# Basic customization
python3 zonerama-downloader.py -d ~/Photos -u

# Full customization  
python3 zonerama-downloader.py --download-dir /backup/zonerama --unzip --delete
```

For programmatic use, you can also customize by modifying the script:

```python
downloader = ZoneramaDownloader(download_dir="my_custom_folder")
downloader.run(unzip_albums=True, delete_zips=True)
```

## Notes

- The script keeps the browser open after downloads are initiated so you can monitor progress and ensure downloads complete
- Downloads are initiated by clicking the download buttons; actual download speed depends on your connection and Zonerama's servers
- The script handles both Czech and English versions of the Zonerama interface
- **Duplicate detection**: Already downloaded albums are automatically skipped
- **Original quality**: The script automatically enables "original photos" option for best quality
- **Unzip safety**: The script only processes ZIP files larger than 1KB to avoid corrupted files

## License

This project is for educational purposes. Please respect Zonerama's terms of service and only download content you own or have permission to download.
