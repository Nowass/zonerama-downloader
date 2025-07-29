# Zonerama Downloader

A Python tool to automatically download all albums from Zonerama.com using Selenium WebDriver.

## Features

- **Automatic album discovery**: Finds all albums on your Zonerama page
- **Duplicate detection**: Skips albums that are already downloaded (supports diacritic normalization)
- **Smart download management**: Handles download timeouts and retries
- **Configurable download location**: Set custom download directory via CLI
- **Auto-unzip functionality**: Automatically extract all ZIP files in the download directory
- **ZIP cleanup option**: Delete ZIP files after successful extraction
- **Browser session persistence**: Keeps browser open for efficient batch downloads
- **Cookie handling**: Automatically handles cookie consent modals
- **Progress tracking**: Shows download progress and statistics
- **CLI interface**: Full command-line interface with flexible options
- **Modular architecture**: Clean, maintainable code structure

## Architecture

This project is available in two versions:

### 1. Modular Version (Recommended) - `main.py`
- **Clean architecture**: Separated into logical modules for better maintainability
- **Easy to extend**: Modular design makes it simple to add new features
- **Better testing**: Each module can be tested independently
- **Type safety**: Improved code organization with clear interfaces

**Structure:**
```
src/
├── __init__.py      # Package initialization
├── config.py        # Configuration management
├── cli.py           # Command line interface
├── file_utils.py    # File operations and utilities
├── scraper.py       # Web scraping with Selenium
└── downloader.py    # Main download orchestration
```

### 2. Legacy Version - `zonerama-downloader.py`
- **Single file**: All functionality in one monolithic script
- **Simple deployment**: Easy to distribute as single file
- **Legacy compatibility**: Maintains original interface

Both versions provide exactly the same functionality and CLI interface.

## Requirements

- Python 3.6+
- Chrome browser
- ChromeDriver (automatically managed by Selenium)
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd zonerama-downloader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Modular Version (Recommended)
```bash
# Basic usage
python3 main.py

# With options
python3 main.py -ud --download-dir ~/Downloads/Zonerama
```

### Legacy Version
```bash
# Basic usage
python3 zonerama-downloader.py

# With options
python3 zonerama-downloader.py -ud --download-dir ~/Downloads/Zonerama
```

Both versions support identical command-line interfaces.

### Command Line Options

- `-d, --download-dir`: Set custom download directory (default: `downloads/`)
- `-u, --unzip`: Automatically unzip all ZIP files in the download directory (works with existing files)
- `--delete`: Delete ZIP files after successful unzipping (requires `-u` or `--unzip`)
- `-ud`: Convenient shorthand for `-u --delete` (unzip all ZIPs and delete them after extraction)
- `--version`: Show version information
- `-h, --help`: Show help message

### Examples

```bash
# Download to default directory
python3 main.py

# Download to specific directory
python3 main.py -d ~/MyPhotos

# Download and unzip all ZIP files (keeps ZIP files)
python3 main.py -u

# Download and unzip all ZIP files (deletes ZIP files after extraction)
python3 main.py -ud

# Unzip existing ZIP files only (no downloading)
python3 main.py -u --download-dir ~/ExistingPhotos

# Full explicit form
python3 main.py --download-dir ~/Photos --unzip --delete
```

## How It Works

1. **Browser Setup**: Opens Chrome browser with download preferences
2. **Navigation**: Navigates to Zonerama albums page
3. **Cookie Handling**: Automatically accepts cookie consent if needed
4. **Album Discovery**: Finds all album elements on the page
5. **Duplicate Detection**: Checks if albums already exist (with diacritic normalization)
6. **Download Process**: For each new album:
   - Clicks on album to open it
   - Locates and clicks download button
   - Handles download modal
   - Waits for download completion
   - Returns to album list
7. **Post-processing**: If enabled, unzips all ZIP files in the download directory and optionally deletes ZIPs
8. **Statistics**: Shows final download summary

## Features in Detail

### Duplicate Detection with Diacritic Support
The tool intelligently detects already downloaded albums by comparing names with diacritic normalization. This means albums like "Prázdniny" and "Prazdniny" are recognized as the same album.

### Smart Download Management
- Waits for downloads to complete before proceeding
- Handles browser download timeouts gracefully
- Maintains browser session for efficient batch processing
- Provides detailed progress information

### Flexible Unzipping
- Option to automatically unzip all ZIP files in the download directory
- Works with both newly downloaded and existing ZIP files
- Choice to keep or delete original ZIP files
- Creates properly named directories for each album
- Handles ZIP extraction errors gracefully

### CLI Interface
- Supports short flags (`-u`, `-d`) and long options (`--unzip`, `--download-dir`)
- Special combined flag `-ud` for common use case
- Comprehensive help and usage examples
- Proper argument validation

### Modular Architecture (New Version)
- **Separation of concerns**: Each module handles specific functionality
- **Config management**: Centralized configuration with `Config` class
- **Clean interfaces**: Well-defined module boundaries
- **Easy maintenance**: Code changes are isolated to relevant modules
- **Extensible design**: Simple to add new features or modify behavior

## Module Overview

### `src/config.py`
Manages all configuration settings, URLs, timeouts, and user preferences.

### `src/cli.py`
Handles command-line argument parsing, user interactions, and configuration display.

### `src/file_utils.py`
Provides file operations, path management, ZIP handling, and diacritic normalization.

### `src/scraper.py`
Contains the `ZoneramaScraper` class for all Selenium WebDriver interactions.

### `src/downloader.py`
The main `ZoneramaDownloader` class that orchestrates the entire download process.

### `main.py`
Entry point that ties all modules together and handles application lifecycle.

## Configuration

The tool uses sensible defaults but can be customized:

- **Download Directory**: Default is `downloads/` in current directory
- **Download Timeout**: 300 seconds (5 minutes) per album
- **Browser Timeouts**: 10 seconds for page elements
- **Unzip Behavior**: Disabled by default, enabled with `-u` flag
- **ZIP Deletion**: Disabled by default, enabled with `--delete` flag

## Error Handling

The tool includes robust error handling for:
- Network connectivity issues
- Page loading timeouts
- Missing download buttons
- Corrupted ZIP files
- File system permissions
- Browser crashes

## Troubleshooting

### Common Issues

1. **ChromeDriver issues**: Make sure Chrome browser is installed and up to date
2. **Download timeouts**: Check internet connection and increase timeout if needed
3. **Permission errors**: Ensure write permissions to download directory
4. **Missing albums**: Verify you're logged in to Zonerama in the browser session

### Browser Requirements
- Chrome browser must be installed
- ChromeDriver is automatically managed by Selenium 4.x
- No need to manually install ChromeDriver

## Development

### Using the Modular Version
For development and customization, use the modular version (`main.py`):

1. **Configuration changes**: Edit `src/config.py`
2. **CLI modifications**: Update `src/cli.py`
3. **New file operations**: Add to `src/file_utils.py`
4. **Web scraping changes**: Modify `src/scraper.py`
5. **Download logic**: Update `src/downloader.py`

### Adding New Features
The modular architecture makes it easy to extend functionality:
- Add new CLI options in `cli.py`
- Implement new file operations in `file_utils.py`
- Extend web scraping capabilities in `scraper.py`
- Modify download behavior in `downloader.py`

## Technical Details

- **Selenium WebDriver**: For browser automation
- **Chrome Browser**: Required for download functionality
- **Request handling**: Robust timeout and retry mechanisms
- **File operations**: Safe file handling with proper error checking
- **Unicode support**: Full diacritic normalization for international album names
- **Modular design**: Clean separation of concerns for maintainability

## Contributing

Feel free to submit issues and enhancement requests! The modular architecture makes contributions easier to implement and review.

## License

This project is provided as-is for educational and personal use.
