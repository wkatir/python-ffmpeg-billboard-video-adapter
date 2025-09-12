"""
Video processing module for Campaign Adaptation Software
Specialized in billboard and LED display format adaptation
"""

import os
import logging
from typing import Optional, Dict, Any, List, Tuple
import ffmpeg
from pathlib import Path
import imageio_ffmpeg

from .config import Config
from .utils import get_file_size_mb, safe_filename, format_duration

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Video processing class specialized for campaign adaptation"""
    
    def __init__(self):
        """Initialize the video processor"""
        self.config = Config()
        
        # Get FFmpeg executable path from imageio-ffmpeg
        self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        logger.info(f"Using FFmpeg from: {self.ffmpeg_path}")
        
        # Set FFmpeg path for ffmpeg-python
        os.environ['FFMPEG_BINARY'] = self.ffmpeg_path
        
    # ---------- Core adaptation methods ----------
    
    def adapt_to_format(
        self,
        input_path: str,
        target_w: int,
        target_h: int,
        mode: str = "fit",           # "fit" (pad) or "fill" (crop)
        blur_bg: bool = False,
        legibility_boost: bool = False,
        roi_center: Optional[Tuple[float,float]] = None,   # (cx, cy) relative
        output_path: Optional[str] = None,
        fps: Optional[int] = None
    ) -> str:
        """
        Adapt video to target format with intelligent cropping/padding
        
        Args:
            input_path: Input video path
            target_w, target_h: Target dimensions
            mode: "fit" (preserve aspect, pad) or "fill" (crop to fill)
            blur_bg: Add blurred background (fit mode only)
            legibility_boost: Enhance contrast/sharpness
            roi_center: ROI center for intelligent cropping (cx, cy) [0..1]
            output_path: Output path
            fps: Target FPS
            
        Returns:
            Path to adapted video
        """
        
        if not output_path:
            output_path = os.path.join(self.config.TEMP_DIR, f"{Path(input_path).stem}_adapted.mp4")
        
        logger.info(f"Adapting {input_path} to {target_w}x{target_h} ({mode} mode)")
        
        # Build filter chain
        vf_chain = []
        
        if mode == "fit":
            if blur_bg:
                # Complex filter: blurred background + centered foreground
                filter_complex = (
                    f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
                    f"boxblur=20:2,crop={target_w}:{target_h}[bg];"
                    f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
                )
                self._run_complex_filter(input_path, output_path, filter_complex, fps=fps, legibility_boost=legibility_boost)
                return output_path
            else:
                # Simple pad mode - scale and pad
                vf_chain.append(f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease")
                vf_chain.append(f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color=black")
        else:  # fill (crop)
            # Simplified crop mode - scale to fill and crop center
            vf_chain.append(f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase")
            vf_chain.append(f"crop={target_w}:{target_h}")
        
        # Add legibility enhancement
        if legibility_boost:
            vf_chain.append("eq=contrast=1.05:brightness=0.02:saturation=1.08")
            vf_chain.append("unsharp=lx=5:ly=5:la=0.7")
        
        # Validate and build filter string
        if not vf_chain:
            raise Exception("No video filters generated - this shouldn't happen")
        
        vf = ",".join(vf_chain)
        logger.info(f"Generated video filter chain: {vf}")
        
        # Validate filter string
        if not vf or vf.strip() == "":
            raise Exception("Empty video filter chain generated")
        
        self._run_simple_filter(input_path, output_path, vf, fps=fps)
        return output_path
    
    def batch_adapt(
        self,
        input_path: str,
        profiles: List[Dict[str,Any]],
        mode: str = "fit",
        blur_bg: bool = False,
        legibility_boost: bool = False,
        roi_center: Optional[Tuple[float,float]] = None,
        fps_map: Optional[Dict[str,int]] = None,
        filename_map: Optional[Dict[str,str]] = None,
    ) -> List[str]:
        """
        Batch adapt video to multiple formats
        
        Args:
            input_path: Input video path
            profiles: List of format profiles [{"key": str, "width": int, "height": int}]
            mode: Adaptation mode
            blur_bg: Blur background
            legibility_boost: Enhance legibility
            roi_center: ROI center
            fps_map: FPS per profile
            filename_map: Custom filenames per profile
            
        Returns:
            List of output file paths
        """
        
        outputs = []
        src_name = os.path.basename(input_path)
        
        for profile in profiles:
            key = profile["key"]
            width = profile["width"] 
            height = profile["height"]
            target_fps = (fps_map or {}).get(key)
            
            # Generate output name
            if filename_map and key in filename_map:
                out_name = filename_map[key]
            else:
                out_name = f"{Path(src_name).stem}__{key}.mp4"
            
            out_path = os.path.join(self.config.OUTPUT_DIR, out_name)
            
            # Adapt to this format
            adapted_path = self.adapt_to_format(
                input_path, width, height,
                mode=mode, blur_bg=blur_bg,
                legibility_boost=legibility_boost, 
                roi_center=roi_center,
                output_path=out_path, 
                fps=target_fps
            )
            
            outputs.append(adapted_path)
            logger.info(f"Adapted to {key}: {adapted_path}")
        
        return outputs
    
    # ---------- Utility methods ----------
    
    def extract_frames(
        self, 
        input_path: str, 
        output_dir: str, 
        frame_rate: float = 0.5, 
        fmt: str = "jpg"
    ) -> List[str]:
        """Extract frames from video for AI analysis"""
        os.makedirs(output_dir, exist_ok=True)
        pattern = os.path.join(output_dir, f"frame_%04d.{fmt}")
        
        (ffmpeg.input(input_path)
               .output(pattern, vf=f'fps={frame_rate}', format='image2')
               .overwrite_output()
               .run(cmd=self.ffmpeg_path, quiet=True))
        
        frames = [
            os.path.join(output_dir, f) 
            for f in sorted(os.listdir(output_dir)) 
            if f.endswith(f".{fmt}")
        ]
        
        logger.info(f"Extracted {len(frames)} frames")
        return frames
    
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
        """Create thumbnail from video"""
        if not output_path:
            output_path = os.path.join(self.config.TEMP_DIR, f"{Path(input_path).stem}_thumb.jpg")
        
        (ffmpeg.input(input_path, ss=time_offset)
               .output(output_path, vframes=1, format='image2')
               .overwrite_output()
               .run(cmd=self.ffmpeg_path, quiet=True))
        
        return output_path
    
    def create_preview_clip(self, input_path: str, seconds: int = 3) -> str:
        """Create short preview clip"""
        info = self.get_video_info(input_path)
        mid_time = max(1.0, info.get("duration", 10) / 2.0 - seconds / 2.0)
        out_path = os.path.join(self.config.TEMP_DIR, f"{Path(input_path).stem}_preview.mp4")
        
        (ffmpeg.input(input_path, ss=mid_time, t=seconds)
               .output(out_path, vcodec='libx264', acodec='aac', movflags='+faststart', preset='medium')
               .overwrite_output()
               .run(cmd=self.ffmpeg_path, quiet=True))
        
        return out_path
    
    # ---------- Helper methods ----------
    
    def _run_simple_filter(self, input_path: str, output_path: str, vf: str, fps: Optional[int] = None):
        """Run simple video filter"""
        try:
            logger.info(f"Running FFmpeg with filter: {vf}")
            logger.info(f"Input: {input_path}")
            logger.info(f"Output: {output_path}")
            
            # Use the string-based filter approach but with validation
            stream = ffmpeg.input(input_path)
            
            output_args = {
                'vcodec': 'libx264', 
                'acodec': 'aac', 
                'preset': 'fast',
                'pix_fmt': 'yuv420p',
                'movflags': '+faststart'
            }
            
            # Only add vf if it's not empty
            if vf and vf.strip():
                output_args['vf'] = vf
            
            if fps: 
                output_args['r'] = fps
                
            logger.info(f"FFmpeg output args: {output_args}")
            
            (stream.output(output_path, **output_args)
                   .overwrite_output()
                   .run(cmd=self.ffmpeg_path, quiet=False, capture_stdout=True, capture_stderr=True))
            
            logger.info(f"FFmpeg processing completed successfully: {output_path}")
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error in _run_simple_filter: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                stderr_msg = e.stderr.decode('utf-8') if isinstance(e.stderr, bytes) else str(e.stderr)
                logger.error(f"FFmpeg stderr: {stderr_msg}")
                raise Exception(f"FFmpeg processing failed: {stderr_msg}")
            else:
                raise Exception(f"FFmpeg processing failed: {str(e)}")
        except Exception as e:
            logger.error(f"Video processing error in _run_simple_filter: {e}")
            raise Exception(f"Video processing failed: {str(e)}")
    
    def _run_complex_filter(
        self, 
        input_path: str, 
        output_path: str, 
        filter_complex: str, 
        fps: Optional[int] = None, 
        legibility_boost: bool = False
    ):
        """Run complex video filter"""
        stream = ffmpeg.input(input_path)
        fc = filter_complex
        
        if legibility_boost:
            fc = fc + ",eq=contrast=1.05:brightness=0.02:saturation=1.08,unsharp=lx=5:ly=5:la=0.7"
        
        kwargs = {
            'filter_complex': fc, 
            'vcodec': 'libx264', 
            'acodec': 'aac', 
                'movflags': '+faststart',
                'preset': 'medium'
        }
        if fps: 
            kwargs['r'] = fps
            
        (stream.output(output_path, **kwargs)
               .overwrite_output()
               .run(cmd=self.ffmpeg_path, quiet=True))
    
    def _parse_frame_rate(self, frame_rate_str: str) -> float:
        """Parse frame rate string safely"""
        try:
            if '/' in frame_rate_str:
                numerator, denominator = frame_rate_str.split('/')
                return float(numerator) / float(denominator) if float(denominator) != 0 else 0.0
            return float(frame_rate_str)
        except (ValueError, ZeroDivisionError):
            return 0.0
