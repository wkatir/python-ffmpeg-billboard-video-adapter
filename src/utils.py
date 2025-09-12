"""
Utility functions for the Campaign Adaptation Software
"""

import os
import tempfile
import shutil
import logging
import json
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import streamlit as st

# Configure logger
logger = logging.getLogger(__name__)

def ensure_dirs() -> None:
    """Ensure necessary directories exist for the application.
    
    Creates temp/, output/, and logs/ directories if they don't exist.
    """
    directories = ["temp", "output", "logs"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)



def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB, 0.0 if file doesn't exist or error occurs
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0.0

def create_temp_file(suffix: str = ".tmp") -> str:
    """Create a temporary file and return its path.
    
    Args:
        suffix: File extension suffix for the temporary file
        
    Returns:
        Path to the created temporary file
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.close()
    return temp_file.name

def cleanup_temp_files(file_paths: List[str]) -> None:
    """Clean up temporary files.
    
    Args:
        file_paths: List of file paths to delete
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {str(e)}")

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (HH:MM:SS or MM:SS)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_int = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds_int:02d}"
    else:
        return f"{minutes:02d}:{seconds_int:02d}"

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing problematic characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename with problematic characters replaced
    """
    # Remove or replace problematic characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    safe_name = "".join(c if c in safe_chars else "_" for c in filename)
    
    # Ensure filename is not too long
    if len(safe_name) > 200:
        name_part = safe_name[:190]
        extension = safe_name.split('.')[-1] if '.' in safe_name else ""
        safe_name = f"{name_part}.{extension}" if extension else name_part
    
    return safe_name




def validate_ffmpeg_installation() -> bool:
    """Check if FFmpeg is properly installed and accessible.
    
    Returns:
        True if FFmpeg is available, False otherwise
    """
    try:
        import imageio_ffmpeg
        # Get FFmpeg executable path
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        return os.path.exists(ffmpeg_path)
    except Exception as e:
        logger.error(f"FFmpeg validation failed: {str(e)}")
        return False


def write_zip(output_files: List[str], zip_path: str) -> str:
    """Create ZIP file with output files.
    
    Args:
        output_files: List of file paths to include in ZIP
        zip_path: Path for the output ZIP file
        
    Returns:
        Path to the created ZIP file
    """
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in output_files:
            if os.path.exists(file_path):
                zf.write(file_path, arcname=os.path.basename(file_path))
    return zip_path


def cleanup_old_files(directory: str, max_age_hours: int = 24, pattern: str = "tmp*") -> int:
    """Clean up old temporary files from a directory.
    
    Args:
        directory: Directory to clean up
        max_age_hours: Maximum age in hours before files are deleted
        pattern: Glob pattern for files to clean up
        
    Returns:
        Number of files cleaned up
    """
    import glob
    import time
    
    if not os.path.exists(directory):
        return 0
        
    files_cleaned = 0
    max_age_seconds = max_age_hours * 3600
    current_time = time.time()
    
    pattern_path = os.path.join(directory, pattern)
    for file_path in glob.glob(pattern_path):
        try:
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                os.remove(file_path)
                files_cleaned += 1
                logger.info(f"Cleaned up old file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {str(e)}")
            
    return files_cleaned

