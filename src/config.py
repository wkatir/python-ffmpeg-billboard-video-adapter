"""
Configuration management for the Campaign Adaptation Software
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, List
import streamlit as st

@dataclass
class Config:
    """Application configuration class for Campaign Adaptation Software"""
    
    # Video processing settings
    DEFAULT_OUTPUT_FORMAT: str = "mp4"
    DEFAULT_QUALITY: str = "high"
    SUPPORTED_FORMATS: List[str] = field(default_factory=list)
    QUALITY_SETTINGS: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # File size limits (in MB)
    MAX_FILE_SIZE: int = 500
    
    # Directory settings
    BASE_DIR: str = field(default_factory=os.getcwd)
    TEMP_DIR: str = ""
    OUTPUT_DIR: str = ""
    LOG_DIR: str = ""
    
    # Campaign adaptation settings
    DEFAULT_ADAPTATION_MODE: str = "fill"  # "fit" or "fill"
    DEFAULT_BLUR_BACKGROUND: bool = False
    DEFAULT_LEGIBILITY_BOOST: bool = True
    DEFAULT_AI_GUIDED_CROP: bool = False
    
    # AI settings
    DEFAULT_SAMPLE_FPS: float = 0.6
    MAX_AI_FRAMES: int = 10
    
    def __post_init__(self):
        """Initialize configuration after object creation"""
        
        # Supported video formats
        self.SUPPORTED_FORMATS = [
            'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'
        ]
        
        # Quality settings for FFmpeg (optimized for campaign content)
        self.QUALITY_SETTINGS = {
            "low": {
                "video_bitrate": "500k",
                "audio_bitrate": "64k",
                "fps": 24
            },
            "medium": {
                "video_bitrate": "1000k",
                "audio_bitrate": "128k",
                "fps": 30
            },
            "high": {
                "video_bitrate": "2000k",
                "audio_bitrate": "192k",
                "fps": 30
            },
            "ultra": {
                "video_bitrate": "4000k",
                "audio_bitrate": "320k",
                "fps": 60
            }
        }
        
        # Set directories
        self.TEMP_DIR = os.environ.get("TEMP_DIR", os.path.join(self.BASE_DIR, "temp"))
        self.OUTPUT_DIR = os.environ.get("OUTPUT_DIR", os.path.join(self.BASE_DIR, "output"))
        self.LOG_DIR = os.environ.get("LOG_DIR", os.path.join(self.BASE_DIR, "logs"))
        
        # Ensure directories exist
        for directory in (self.TEMP_DIR, self.OUTPUT_DIR, self.LOG_DIR):
            os.makedirs(directory, exist_ok=True)
    
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
