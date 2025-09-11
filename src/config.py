"""
Configuration management for the FFmpeg Billboard Video Adapter
"""

import os
from dataclasses import dataclass
from typing import Dict, Any
import streamlit as st

@dataclass
class Config:
    """Application configuration class"""
    
    # Video processing settings
    DEFAULT_OUTPUT_FORMAT: str = "mp4"
    DEFAULT_QUALITY: str = "high"
    SUPPORTED_FORMATS: list = None
    QUALITY_SETTINGS: Dict[str, Dict[str, Any]] = None
    
    # File size limits (in MB)
    MAX_FILE_SIZE: int = 500
    
    # Temporary directory settings
    TEMP_DIR: str = None
    
    def __post_init__(self):
        """Initialize configuration after object creation"""
        
        # Supported video formats
        self.SUPPORTED_FORMATS = [
            'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'
        ]
        
        # Quality settings for FFmpeg
        self.QUALITY_SETTINGS = {
            "low": {
                "video_bitrate": "500k",
                "audio_bitrate": "64k",
                "scale": "640:480",
                "fps": 24
            },
            "medium": {
                "video_bitrate": "1000k",
                "audio_bitrate": "128k",
                "scale": "1280:720",
                "fps": 30
            },
            "high": {
                "video_bitrate": "2000k",
                "audio_bitrate": "192k",
                "scale": "1920:1080",
                "fps": 30
            },
            "ultra": {
                "video_bitrate": "4000k",
                "audio_bitrate": "320k",
                "scale": "1920:1080",
                "fps": 60
            }
        }
        
        # Set temporary directory
        self.TEMP_DIR = os.environ.get("TEMP_DIR", os.path.join(os.getcwd(), "temp"))
        
        # Ensure temp directory exists
        os.makedirs(self.TEMP_DIR, exist_ok=True)
    
    def get_quality_settings(self, quality: str) -> Dict[str, Any]:
        """Get quality settings for the specified quality level"""
        return self.QUALITY_SETTINGS.get(quality, self.QUALITY_SETTINGS["medium"])
    
    def is_supported_format(self, file_extension: str) -> bool:
        """Check if the file format is supported"""
        return file_extension.lower() in self.SUPPORTED_FORMATS
    
    def get_gemini_api_key(self) -> str:
        """Get Gemini API key from environment or Streamlit secrets"""
        # Try environment variable first
        api_key = os.environ.get("GOOGLE_API_KEY")
        
        # Try Streamlit secrets if environment variable not found
        if not api_key:
            try:
                api_key = st.secrets.get("GOOGLE_API_KEY")
            except:
                pass
        
        return api_key or ""
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate current configuration"""
        validation_results = {
            "temp_directory_exists": os.path.exists(self.TEMP_DIR),
            "temp_directory_writable": os.access(self.TEMP_DIR, os.W_OK),
            "gemini_api_key_available": bool(self.get_gemini_api_key()),
        }
        
        return validation_results
