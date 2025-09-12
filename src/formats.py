"""
Format profiles for billboard and LED display adaptations
"""

from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class FormatProfile:
    """Profile for a specific display format"""
    key: str
    width: int
    height: int
    fps: int = 30
    description: str = ""

# Standard LED/Billboard formats
STANDARD_FORMATS = {
    "LED_16x9_FHD": FormatProfile(
        "LED_16x9_FHD", 1920, 1080, 30, 
        "Full HD 16:9 LED Display"
    ),
    "LED_9x16_FHD": FormatProfile(
        "LED_9x16_FHD", 1080, 1920, 30, 
        "Full HD 9:16 Portrait LED Display"
    ),
    "LED_4x3_XGA": FormatProfile(
        "LED_4x3_XGA", 1024, 768, 30, 
        "XGA 4:3 LED Display"
    ),
    "LED_960x320": FormatProfile(
        "LED_960x320", 960, 320, 30, 
        "Ultra-wide LED Strip Display"
    ),
    "LED_256x128": FormatProfile(
        "LED_256x128", 256, 128, 25, 
        "Low-res LED Matrix Display"
    ),
    "LED_1280x720": FormatProfile(
        "LED_1280x720", 1280, 720, 30, 
        "HD 16:9 LED Display"
    ),
    "LED_800x600": FormatProfile(
        "LED_800x600", 800, 600, 30, 
        "SVGA 4:3 LED Display"
    ),
    "LED_1024x1024": FormatProfile(
        "LED_1024x1024", 1024, 1024, 30, 
        "Square LED Display"
    ),
}

# Digital Billboard formats
BILLBOARD_FORMATS = {
    "BILLBOARD_14x48": FormatProfile(
        "BILLBOARD_14x48", 1680, 480, 30, 
        "Standard Billboard 14'x48'"
    ),
    "BILLBOARD_12x24": FormatProfile(
        "BILLBOARD_12x24", 1440, 720, 30, 
        "Junior Billboard 12'x24'"
    ),
    "BILLBOARD_6x12": FormatProfile(
        "BILLBOARD_6x12", 720, 360, 30, 
        "Poster Billboard 6'x12'"
    ),
}

# Social Media / Digital formats (for comparison)
SOCIAL_FORMATS = {
    "INSTAGRAM_SQUARE": FormatProfile(
        "INSTAGRAM_SQUARE", 1080, 1080, 30, 
        "Instagram Square Post"
    ),
    "INSTAGRAM_STORY": FormatProfile(
        "INSTAGRAM_STORY", 1080, 1920, 30, 
        "Instagram Story"
    ),
    "YOUTUBE_16x9": FormatProfile(
        "YOUTUBE_16x9", 1920, 1080, 30, 
        "YouTube 16:9 Video"
    ),
    "TIKTOK_9x16": FormatProfile(
        "TIKTOK_9x16", 1080, 1920, 30, 
        "TikTok Portrait Video"
    ),
}

# Combine all formats
ALL_FORMATS = {
    **STANDARD_FORMATS,
    **BILLBOARD_FORMATS, 
    **SOCIAL_FORMATS
}

def get_format_by_key(key: str) -> FormatProfile:
    """Get format profile by key"""
    return ALL_FORMATS.get(key)

def get_formats_by_aspect_ratio(aspect_ratio: str) -> List[FormatProfile]:
    """Get all formats matching a specific aspect ratio"""
    formats = []
    
    for profile in ALL_FORMATS.values():
        if aspect_ratio == "16:9" and abs((profile.width / profile.height) - (16/9)) < 0.1:
            formats.append(profile)
        elif aspect_ratio == "9:16" and abs((profile.width / profile.height) - (9/16)) < 0.1:
            formats.append(profile)
        elif aspect_ratio == "4:3" and abs((profile.width / profile.height) - (4/3)) < 0.1:
            formats.append(profile)
        elif aspect_ratio == "1:1" and abs((profile.width / profile.height) - 1.0) < 0.1:
            formats.append(profile)
    
    return formats

def create_custom_format(key: str, width: int, height: int, fps: int = 30, description: str = "") -> FormatProfile:
    """Create a custom format profile"""
    return FormatProfile(key, width, height, fps, description or f"Custom {width}x{height}")

def get_format_categories() -> Dict[str, List[str]]:
    """Get formats organized by category"""
    return {
        "LED Displays": list(STANDARD_FORMATS.keys()),
        "Billboards": list(BILLBOARD_FORMATS.keys()),
        "Social Media": list(SOCIAL_FORMATS.keys())
    }
