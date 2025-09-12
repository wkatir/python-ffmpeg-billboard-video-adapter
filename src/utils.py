"""
Utility functions for the Campaign Adaptation Software
"""

import os
import tempfile
import shutil
import logging
import time
import json
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import streamlit as st

# Configure logger
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure necessary directories exist"""
    directories = ["temp", "output", "logs"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def setup_environment():
    """Setup the application environment"""
    ensure_dirs()
    
    # Setup logging
    log_file = os.path.join("logs", "app.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Campaign Adaptation Software environment setup completed")

def validate_file_type(uploaded_file) -> bool:
    """Validate if the uploaded file is a supported video format"""
    
    if not uploaded_file:
        return False
    
    # Get file extension
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    # Supported formats
    supported_formats = ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v']
    
    return file_extension in supported_formats

def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes"""
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0.0

def create_temp_file(suffix: str = ".tmp") -> str:
    """Create a temporary file and return its path"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.close()
    return temp_file.name

def cleanup_temp_files(file_paths: List[str]):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {str(e)}")

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing problematic characters"""
    # Remove or replace problematic characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    safe_name = "".join(c if c in safe_chars else "_" for c in filename)
    
    # Ensure filename is not too long
    if len(safe_name) > 200:
        name_part = safe_name[:190]
        extension = safe_name.split('.')[-1] if '.' in safe_name else ""
        safe_name = f"{name_part}.{extension}" if extension else name_part
    
    return safe_name

def check_disk_space(path: str, required_mb: float) -> bool:
    """Check if there's enough disk space available"""
    try:
        free_bytes = shutil.disk_usage(path).free
        free_mb = free_bytes / (1024 * 1024)
        return free_mb >= required_mb
    except Exception as e:
        logger.warning(f"Could not check disk space: {str(e)}")
        return True  # Assume space is available if we can't check

def display_file_info(file_path: str) -> dict:
    """Get comprehensive file information"""
    try:
        stat = os.stat(file_path)
        file_info = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size_mb": stat.st_size / (1024 * 1024),
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
            "extension": Path(file_path).suffix.lower()
        }
        return file_info
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {str(e)}")
        return {}

def show_progress(current: int, total: int, message: str = "Processing"):
    """Show progress in Streamlit"""
    progress = current / total if total > 0 else 0
    st.progress(progress)
    st.text(f"{message}: {current}/{total} ({progress*100:.1f}%)")

def validate_ffmpeg_installation() -> bool:
    """Check if FFmpeg is properly installed and accessible"""
    try:
        import imageio_ffmpeg
        # Get FFmpeg executable path
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        return os.path.exists(ffmpeg_path)
    except Exception as e:
        logger.error(f"FFmpeg validation failed: {str(e)}")
        return False

def versioned_output_name(src_name: str, profile_key: str, suffix: str = ".mp4") -> str:
    """Create versioned output filename"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base = Path(src_name).stem
    return safe_filename(f"{base}__{profile_key}__{timestamp}{suffix}")

def write_zip(output_files: List[str], zip_path: str) -> str:
    """Create ZIP file with output files"""
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in output_files:
            if os.path.exists(file_path):
                zf.write(file_path, arcname=os.path.basename(file_path))
    return zip_path

def get_video_info(file_path: str) -> dict:
    """Get video file information using FFmpeg"""
    try:
        import ffmpeg
        import imageio_ffmpeg
        
        # Get FFmpeg executable path
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        probe = ffmpeg.probe(file_path, cmd=ffmpeg_path)
        
        video_info = {
            "duration": float(probe.get('format', {}).get('duration', 0)),
            "size": int(probe.get('format', {}).get('size', 0)),
            "bit_rate": int(probe.get('format', {}).get('bit_rate', 0)),
            "format_name": probe.get('format', {}).get('format_name', 'unknown')
        }
        
        # Get video stream info
        video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
        if video_streams:
            video_stream = video_streams[0]
            # Fix the unsafe eval usage
            frame_rate_str = video_stream.get('r_frame_rate', '0/1')
            try:
                if '/' in frame_rate_str:
                    numerator, denominator = frame_rate_str.split('/')
                    fps = float(numerator) / float(denominator) if float(denominator) != 0 else 0.0
                else:
                    fps = float(frame_rate_str)
            except (ValueError, ZeroDivisionError):
                fps = 0.0
                
            video_info.update({
                "width": video_stream.get('width', 0),
                "height": video_stream.get('height', 0),
                "fps": fps,
                "codec": video_stream.get('codec_name', 'unknown')
            })
        
        return video_info
        
    except Exception as e:
        logger.error(f"Error getting video info for {file_path}: {str(e)}")
        return {}
