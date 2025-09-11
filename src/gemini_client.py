"""
Google Gemini AI client for video analysis
"""

import os
import logging
import tempfile
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import streamlit as st
from pathlib import Path

from .config import Config
from .video_processor import VideoProcessor
from .utils import create_temp_file, cleanup_temp_files

logger = logging.getLogger(__name__)

class GeminiClient:
    """Google Gemini AI client for video analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google Gemini API key
        """
        
        self.config = Config()
        self.api_key = api_key or self.config.get_gemini_api_key()
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        logger.info("Gemini client initialized successfully")
    
    def test_connection(self) -> bool:
        """Test connection to Gemini API"""
        try:
            response = self.model.generate_content(
                "Hello, this is a test message.",
                safety_settings=self.safety_settings
            )
            return bool(response.text)
        except Exception as e:
            logger.error(f"Gemini connection test failed: {str(e)}")
            return False
    
    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Analyze video content using Gemini AI
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary containing analysis results
        """
        
        try:
            logger.info(f"Starting video analysis for: {video_path}")
            
            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🤖 Preparing video for AI analysis...")
            progress_bar.progress(0.1)
            
            # Extract frames for analysis (Gemini works better with images)
            video_processor = VideoProcessor()
            temp_frames_dir = tempfile.mkdtemp()
            
            try:
                # Extract frames at 1 frame per second
                frame_files = video_processor.extract_frames(
                    video_path, 
                    temp_frames_dir, 
                    frame_rate=0.5,  # Extract every 2 seconds
                    format="jpg"
                )
                
                progress_bar.progress(0.3)
                status_text.text("🔍 Analyzing video content with AI...")
                
                # Analyze frames (limit to first 10 frames to avoid API limits)
                analysis_results = []
                max_frames = min(10, len(frame_files))
                
                for i, frame_path in enumerate(frame_files[:max_frames]):
                    try:
                        frame_analysis = self._analyze_frame(frame_path, i)
                        if frame_analysis:
                            analysis_results.append(frame_analysis)
                        
                        # Update progress
                        progress = 0.3 + (0.6 * (i + 1) / max_frames)
                        progress_bar.progress(progress)
                        
                    except Exception as e:
                        logger.warning(f"Failed to analyze frame {i}: {str(e)}")
                        continue
                
                progress_bar.progress(0.9)
                status_text.text("📊 Compiling analysis results...")
                
                # Compile comprehensive analysis
                comprehensive_analysis = self._compile_video_analysis(
                    analysis_results, 
                    video_processor.get_video_info(video_path)
                )
                
                progress_bar.progress(1.0)
                status_text.text("✅ AI analysis completed!")
                
                return comprehensive_analysis
                
            finally:
                # Cleanup extracted frames
                cleanup_temp_files([os.path.join(temp_frames_dir, f) for f in os.listdir(temp_frames_dir)])
                os.rmdir(temp_frames_dir)
                
        except Exception as e:
            logger.error(f"Video analysis failed: {str(e)}")
            return {
                "error": str(e),
                "summary": "Analysis failed due to an error.",
                "details": {"error_message": str(e)}
            }
    
    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a single image
        
        Args:
            image_path: Path to image file
            prompt: Optional custom prompt for analysis
            
        Returns:
            Dictionary containing analysis results
        """
        
        try:
            # Default prompt for image analysis
            if not prompt:
                prompt = """
                Analyze this image and provide:
                1. A brief description of what you see
                2. Key objects, people, or elements present
                3. The setting or context
                4. Any notable activities or actions
                5. Overall mood or atmosphere
                
                Be concise but informative.
                """
            
            # Upload image to Gemini
            uploaded_file = genai.upload_file(path=image_path)
            
            # Generate analysis
            response = self.model.generate_content(
                [uploaded_file, prompt],
                safety_settings=self.safety_settings
            )
            
            # Clean up uploaded file
            genai.delete_file(uploaded_file.name)
            
            return {
                "analysis": response.text,
                "image_path": image_path,
                "timestamp": os.path.getctime(image_path)
            }
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def generate_video_summary(self, analysis_results: List[Dict[str, Any]]) -> str:
        """
        Generate a comprehensive video summary from frame analyses
        
        Args:
            analysis_results: List of frame analysis results
            
        Returns:
            Comprehensive video summary
        """
        
        try:
            # Compile all frame analyses
            frame_descriptions = []
            for i, result in enumerate(analysis_results):
                if "analysis" in result:
                    frame_descriptions.append(f"Frame {i+1}: {result['analysis']}")
            
            # Create summary prompt
            prompt = f"""
            Based on the following frame-by-frame analysis of a video, create a comprehensive summary:
            
            {chr(10).join(frame_descriptions)}
            
            Please provide:
            1. A concise overall summary of the video content
            2. Key themes or subjects throughout the video
            3. Notable changes or progression in the video
            4. Any interesting patterns or observations
            
            Keep the summary informative but concise.
            """
            
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return f"Unable to generate summary: {str(e)}"
    
    def _analyze_frame(self, frame_path: str, frame_number: int) -> Optional[Dict[str, Any]]:
        """Analyze a single video frame"""
        
        try:
            prompt = f"""
            This is frame {frame_number + 1} from a video. Analyze this frame and describe:
            1. What objects, people, or elements are visible
            2. The setting or environment
            3. Any actions or activities taking place
            4. Notable colors, lighting, or visual elements
            
            Be concise and focus on the most important elements.
            """
            
            result = self.analyze_image(frame_path, prompt)
            result["frame_number"] = frame_number
            
            return result
            
        except Exception as e:
            logger.error(f"Frame analysis failed for frame {frame_number}: {str(e)}")
            return None
    
    def _compile_video_analysis(
        self, 
        frame_analyses: List[Dict[str, Any]], 
        video_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile comprehensive video analysis from frame analyses"""
        
        try:
            # Generate summary
            summary = self.generate_video_summary(frame_analyses)
            
            # Extract key information
            successful_analyses = [a for a in frame_analyses if "analysis" in a and not "error" in a]
            
            # Compile details
            details = {
                "total_frames_analyzed": len(successful_analyses),
                "video_duration": video_info.get("duration_formatted", "Unknown"),
                "video_resolution": f"{video_info.get('width', 0)}x{video_info.get('height', 0)}",
                "video_codec": video_info.get("video_codec", "Unknown"),
                "file_size": f"{video_info.get('file_size_mb', 0):.2f} MB"
            }
            
            # Create comprehensive result
            result = {
                "summary": summary,
                "details": details,
                "frame_analyses": successful_analyses,
                "video_info": video_info,
                "analysis_metadata": {
                    "frames_processed": len(successful_analyses),
                    "analysis_success_rate": len(successful_analyses) / len(frame_analyses) if frame_analyses else 0,
                    "model_used": "gemini-1.5-flash"
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to compile video analysis: {str(e)}")
            return {
                "error": str(e),
                "summary": "Failed to compile comprehensive analysis",
                "details": {"error": str(e)}
            }
