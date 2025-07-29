"""
File utilities for Zonerama Downloader

Handles file operations, path management, and ZIP processing
"""

import os
import zipfile
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


def normalize_text(text):
    """Remove diacritics and normalize text for comparison
    
    Args:
        text (str): Text to normalize
        
    Returns:
        str: Normalized text without diacritics
    """
    # Remove diacritics by decomposing and filtering combining characters
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')


def sanitize_filename(filename):
    """Sanitize filename for filesystem compatibility
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove or replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure it's not empty
    if not filename:
        filename = "unnamed"
    
    return filename


def ensure_directory_exists(directory_path):
    """Ensure directory exists, create if it doesn't
    
    Args:
        directory_path (str): Path to directory
        
    Returns:
        Path: Path object for the directory
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_absolute_path(path_str):
    """Convert path string to absolute path
    
    Args:
        path_str (str): Path string (can be relative or absolute)
        
    Returns:
        str: Absolute path
    """
    return str(Path(path_str).expanduser().resolve())


def list_zip_files(directory):
    """List all ZIP files in directory
    
    Args:
        directory (str): Directory path to search
        
    Returns:
        list: List of ZIP file paths
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        return []
    
    return [str(f) for f in directory_path.glob("*.zip")]


def is_valid_zip_file(zip_path):
    """Check if file is a valid ZIP file
    
    Args:
        zip_path (str): Path to ZIP file
        
    Returns:
        bool: True if valid ZIP file, False otherwise
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Try to read the file list to validate the ZIP
            zip_file.namelist()
            return True
    except (zipfile.BadZipFile, FileNotFoundError, PermissionError):
        return False


def unzip_file(zip_path, extract_to=None, delete_after=False):
    """Unzip a file to specified directory
    
    Args:
        zip_path (str): Path to ZIP file
        extract_to (str, optional): Directory to extract to. If None, extracts to same directory as ZIP
        delete_after (bool): Whether to delete ZIP file after successful extraction
        
    Returns:
        tuple: (success: bool, extract_path: str, error_message: str or None)
    """
    zip_path = Path(zip_path)
    
    if not zip_path.exists():
        return False, "", f"ZIP file not found: {zip_path}"
    
    if not is_valid_zip_file(str(zip_path)):
        return False, "", f"Invalid ZIP file: {zip_path}"
    
    # Determine extraction directory
    if extract_to is None:
        extract_to = zip_path.parent
    else:
        extract_to = Path(extract_to)
    
    # Create album directory based on ZIP filename (without .zip extension)
    album_name = zip_path.stem
    album_dir = extract_to / album_name
    
    try:
        # Ensure extraction directory exists
        album_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            zip_file.extractall(album_dir)
        
        # Delete ZIP file if requested
        if delete_after:
            try:
                zip_path.unlink()
            except (PermissionError, FileNotFoundError) as e:
                # Continue even if deletion fails
                print(f"⚠️  Warning: Could not delete ZIP file {zip_path}: {e}")
        
        return True, str(album_dir), None
        
    except Exception as e:
        return False, "", f"Error extracting {zip_path}: {str(e)}"


def find_existing_albums(download_dir, album_name):
    """Find existing albums (both ZIP and extracted directories) that match the given name
    
    Args:
        download_dir (str): Download directory to search
        album_name (str): Album name to search for
        
    Returns:
        dict: Dictionary with 'zip_files' and 'directories' lists
    """
    download_path = Path(download_dir)
    if not download_path.exists():
        return {'zip_files': [], 'directories': []}
    
    normalized_album_name = normalize_text(album_name.lower())
    found_items = {'zip_files': [], 'directories': []}
    
    try:
        for item in download_path.iterdir():
            item_name_normalized = normalize_text(item.name.lower())
            
            if item.is_file() and item.suffix.lower() == '.zip':
                # Check ZIP files (remove .zip extension for comparison)
                zip_name_normalized = normalize_text(item.stem.lower())
                if zip_name_normalized == normalized_album_name:
                    found_items['zip_files'].append(str(item))
            
            elif item.is_dir():
                # Check directories
                if item_name_normalized == normalized_album_name:
                    found_items['directories'].append(str(item))
    
    except (PermissionError, OSError):
        # Return empty results if we can't read the directory
        pass
    
    return found_items


def is_album_already_downloaded(download_dir, album_name):
    """Check if album is already downloaded (either as ZIP or extracted directory)
    
    Args:
        download_dir (str): Download directory to check
        album_name (str): Album name to check for
        
    Returns:
        bool: True if album already exists, False otherwise
    """
    existing = find_existing_albums(download_dir, album_name)
    return len(existing['zip_files']) > 0 or len(existing['directories']) > 0


def get_file_size_mb(file_path):
    """Get file size in megabytes
    
    Args:
        file_path (str): Path to file
        
    Returns:
        float: File size in MB, or 0 if file doesn't exist
    """
    try:
        size_bytes = Path(file_path).stat().st_size
        return round(size_bytes / (1024 * 1024), 2)
    except (FileNotFoundError, OSError):
        return 0


def count_files_in_directory(directory_path):
    """Count number of files in directory (non-recursive)
    
    Args:
        directory_path (str): Directory path
        
    Returns:
        int: Number of files in directory
    """
    try:
        path = Path(directory_path)
        if not path.exists() or not path.is_dir():
            return 0
        return len([f for f in path.iterdir() if f.is_file()])
    except (PermissionError, OSError):
        return 0
