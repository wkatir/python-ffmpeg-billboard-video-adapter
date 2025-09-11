"""
Video processing module using FFmpeg
"""

import os
import logging
import tempfile
from typing import Optional, Dict, Any, Tuple
import ffmpeg
import streamlit as st
from pathlib import Path
import imageio_ffmpeg

from .config import Config
from .utils import create_temp_file, get_file_size_mb, safe_filename, format_duration

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Video processing class using FFmpeg"""
    
    def __init__(self):
        """Initialize the video processor"""
        self.config = Config()
        
        # Get FFmpeg executable path from imageio-ffmpeg
        self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        logger.info(f"Using FFmpeg from: {self.ffmpeg_path}")
        
        # Set FFmpeg path for ffmpeg-python
        os.environ['FFMPEG_BINARY'] = self.ffmpeg_path
        
    def convert_video(
        self,
        input_path: str,
        output_format: str = "mp4",
        quality: str = "medium",
        output_path: Optional[str] = None
    ) -> str:
        """
        Convert video to specified format and quality
        
        Args:
            input_path: Path to input video file
            output_format: Output format (mp4, avi, mov, etc.)
            quality: Quality setting (low, medium, high, ultra)
            output_path: Optional output path, if not provided, will be generated
            
        Returns:
            Path to the converted video file
        """
        
        try:
            # Generate output path if not provided
            if not output_path:
                input_name = Path(input_path).stem
                safe_name = safe_filename(f"{input_name}_converted.{output_format}")
                output_path = os.path.join(self.config.TEMP_DIR, safe_name)
            
            # Get quality settings
            quality_settings = self.config.get_quality_settings(quality)
            
            logger.info(f"Converting {input_path} to {output_path} with quality {quality}")
            
            # Build FFmpeg stream
            input_stream = ffmpeg.input(input_path)
            
            # Apply video filters and encoding settings
            video_stream = input_stream.video
            audio_stream = input_stream.audio
            
            # Video encoding options
            video_options = {
                'vcodec': 'libx264',
                'video_bitrate': quality_settings['video_bitrate'],
                'vf': f"scale={quality_settings['scale']}",
                'r': quality_settings['fps']
            }
            
            # Audio encoding options
            audio_options = {
                'acodec': 'aac',
                'audio_bitrate': quality_settings['audio_bitrate']
            }
            
            # Create output stream
            output_stream = ffmpeg.output(
                video_stream,
                audio_stream,
                output_path,
                **video_options,
                **audio_options,
                **self._get_format_specific_options(output_format)
            )
            
            # Run conversion with progress tracking
            self._run_ffmpeg_with_progress(output_stream, input_path)
            
            logger.info(f"Video conversion completed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting video: {str(e)}")
            raise Exception(f"Video conversion failed: {str(e)}")
    
    def extract_frames(
        self,
        input_path: str,
        output_dir: str,
        frame_rate: float = 1.0,
        format: str = "jpg"
    ) -> list:
        """
        Extract frames from video
        
        Args:
            input_path: Path to input video file
            output_dir: Directory to save extracted frames
            frame_rate: Frames per second to extract
            format: Output image format (jpg, png, etc.)
            
        Returns:
            List of extracted frame file paths
        """
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            output_pattern = os.path.join(output_dir, f"frame_%04d.{format}")
            
            logger.info(f"Extracting frames from {input_path} at {frame_rate} fps")
            
            # Build FFmpeg command for frame extraction
            (
                ffmpeg
                .input(input_path)
                .output(
                    output_pattern,
                    vf=f'fps={frame_rate}',
                    format='image2'
                )
                .overwrite_output()
                .run(cmd=self.ffmpeg_path, quiet=True)
            )
            
            # Get list of extracted frames
            frame_files = []
            for file in os.listdir(output_dir):
                if file.startswith("frame_") and file.endswith(f".{format}"):
                    frame_files.append(os.path.join(output_dir, file))
            
            frame_files.sort()
            logger.info(f"Extracted {len(frame_files)} frames")
            
            return frame_files
            
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            raise Exception(f"Frame extraction failed: {str(e)}")
    
    def get_video_info(self, input_path: str) -> Dict[str, Any]:
        """
        Get comprehensive video information
        
        Args:
            input_path: Path to video file
            
        Returns:
            Dictionary containing video information
        """
        
        try:
            probe = ffmpeg.probe(input_path, cmd=self.ffmpeg_path)
            
            # Extract format information
            format_info = probe.get('format', {})
            
            # Extract video stream information
            video_streams = [s for s in probe['streams'] if s['codec_type'] == 'video']
            audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
            
            video_info = {
                'filename': os.path.basename(input_path),
                'file_size_mb': get_file_size_mb(input_path),
                'duration': float(format_info.get('duration', 0)),
                'duration_formatted': format_duration(float(format_info.get('duration', 0))),
                'bit_rate': int(format_info.get('bit_rate', 0)),
                'format_name': format_info.get('format_name', 'unknown'),
                'nb_streams': format_info.get('nb_streams', 0)
            }
            
            # Add video stream info
            if video_streams:
                video_stream = video_streams[0]
                video_info.update({
                    'video_codec': video_stream.get('codec_name', 'unknown'),
                    'width': video_stream.get('width', 0),
                    'height': video_stream.get('height', 0),
                    'aspect_ratio': video_stream.get('display_aspect_ratio', 'N/A'),
                    'frame_rate': self._parse_frame_rate(video_stream.get('r_frame_rate', '0/1')),
                    'pixel_format': video_stream.get('pix_fmt', 'unknown')
                })
            
            # Add audio stream info
            if audio_streams:
                audio_stream = audio_streams[0]
                video_info.update({
                    'audio_codec': audio_stream.get('codec_name', 'unknown'),
                    'sample_rate': audio_stream.get('sample_rate', 0),
                    'channels': audio_stream.get('channels', 0),
                    'channel_layout': audio_stream.get('channel_layout', 'unknown')
                })
            
            return video_info
            
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return {'error': str(e)}
    
    def create_thumbnail(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        time_offset: str = "00:00:01"
    ) -> str:
        """
        Create a thumbnail from video
        
        Args:
            input_path: Path to input video file
            output_path: Path for thumbnail output
            time_offset: Time offset for thumbnail (format: HH:MM:SS)
            
        Returns:
            Path to created thumbnail
        """
        
        try:
            if not output_path:
                input_name = Path(input_path).stem
                output_path = os.path.join(self.config.TEMP_DIR, f"{input_name}_thumb.jpg")
            
            logger.info(f"Creating thumbnail for {input_path}")
            
            (
                ffmpeg
                .input(input_path, ss=time_offset)
                .output(output_path, vframes=1, format='image2')
                .overwrite_output()
                .run(cmd=self.ffmpeg_path, quiet=True)
            )
            
            logger.info(f"Thumbnail created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            raise Exception(f"Thumbnail creation failed: {str(e)}")
    
    def _get_format_specific_options(self, format: str) -> Dict[str, Any]:
        """Get format-specific encoding options"""
        
        format_options = {
            'mp4': {
                'movflags': '+faststart',  # Enable fast start for web playback
                'preset': 'medium'
            },
            'avi': {
                'preset': 'medium'
            },
            'mov': {
                'movflags': '+faststart',
                'preset': 'medium'
            },
            'mkv': {
                'preset': 'medium'
            },
            'webm': {
                'vcodec': 'libvpx-vp9',
                'acodec': 'libvorbis'
            }
        }
        
        return format_options.get(format, {})
    
    def _parse_frame_rate(self, frame_rate_str: str) -> float:
        """Parse frame rate string (e.g., '30/1') to float"""
        try:
            if '/' in frame_rate_str:
                numerator, denominator = frame_rate_str.split('/')
                return float(numerator) / float(denominator)
            return float(frame_rate_str)
        except:
            return 0.0
    
    def _run_ffmpeg_with_progress(self, output_stream, input_path: str):
        """Run FFmpeg with progress tracking"""
        
        try:
            # Get video duration for progress calculation
            video_info = self.get_video_info(input_path)
            total_duration = video_info.get('duration', 0)
            
            if total_duration > 0:
                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Run with progress (simplified version)
                # Note: Real progress tracking would require parsing FFmpeg output
                # This is a simplified version for demonstration
                
                status_text.text("🔄 Processing video...")
                progress_bar.progress(0.1)
                
                # Run the actual conversion with custom FFmpeg path
                output_stream.overwrite_output().run(cmd=self.ffmpeg_path, quiet=True)
                
                progress_bar.progress(1.0)
                status_text.text("✅ Video processing completed!")
                
            else:
                # Run without progress tracking
                output_stream.overwrite_output().run(cmd=self.ffmpeg_path, quiet=True)
                
        except Exception as e:
            logger.error(f"FFmpeg execution failed: {str(e)}")
            raise
