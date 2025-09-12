"""
Google Gemini AI client for video analysis and ROI detection
"""

import os
import logging
import tempfile
import json
from typing import Optional, Dict, Any, List, Tuple
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import streamlit as st
from pathlib import Path

from .config import Config
from .utils import create_temp_file, cleanup_temp_files

logger = logging.getLogger(__name__)

class GeminiClient:
    """Google Gemini AI client for video analysis and ROI detection"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google Gemini API key
            model_name: Gemini model to use
        """
        
        self.config = Config()
        self.api_key = api_key or self.config.get_gemini_api_key()
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required for AI-guided features")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(model_name)
        
        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        logger.info("Gemini client initialized successfully for Campaign Adaptation")
    
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
    
    def detect_protected_regions(self, image_path: str) -> List[Dict]:
        """
        Detect regions to protect in an image (logos, text, faces)
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of regions [{x,y,w,h}] in relative coordinates [0..1]
        """
        
        prompt = (
            "Return ONLY JSON with key 'regions' as a list of objects {x, y, w, h} "
            "(all between 0 and 1, relative to image dimensions). "
            "Regions should cover: brand logos/marks, large overlay text, and faces. "
            "Focus on elements that should be preserved when cropping for different aspect ratios. "
            "Do not include any other text or explanation."
        )
        
        try:
            uploaded_file = genai.upload_file(path=image_path)
            
            response = self.model.generate_content(
                [uploaded_file, prompt],
                safety_settings=self.safety_settings,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parse JSON response
            data = {}
            try:
                data = json.loads(response.text or "{}")
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from code block
                text = (response.text or "").strip()
                if text.startswith("```") and text.endswith("```"):
                    text = text.strip("```").strip()
                    if text.startswith("json"):
                        text = text[4:].strip()
                    data = json.loads(text)
                else:
                    data = json.loads(text) if text else {}
            
            return data.get("regions", [])
            
        except Exception as e:
            logger.warning(f"ROI detection failed: {str(e)}")
            return []
        finally:
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass
    
    @staticmethod
    def union_regions(regions: List[Dict]) -> Optional[Tuple[float, float, float, float]]:
        """
        Calculate union of multiple regions
        
        Args:
            regions: List of regions [{x,y,w,h}] in relative coordinates
            
        Returns:
            Union region (x, y, w, h) or None if no regions
        """
        if not regions:
            return None
        
        xs = [r["x"] for r in regions]
        ys = [r["y"] for r in regions]
        x2s = [r["x"] + r["w"] for r in regions]
        y2s = [r["y"] + r["h"] for r in regions]
        
        # Calculate bounding box
        union_x = max(0.0, min(xs))
        union_y = max(0.0, min(ys))
        union_x2 = min(1.0, max(x2s))
        union_y2 = min(1.0, max(y2s))
        
        union_w = max(0.0, union_x2 - union_x)
        union_h = max(0.0, union_y2 - union_y)
        
        return (union_x, union_y, union_w, union_h)
    
    def suggest_crop_center(self, frame_images: List[str]) -> Optional[Tuple[float, float]]:
        """
        Analyze multiple frames and suggest optimal crop center
        
        Args:
            frame_images: List of frame image paths
            
        Returns:
            Suggested center (cx, cy) in relative coordinates [0..1] or None
        """
        all_regions = []
        
        for frame_path in frame_images:
            try:
                regions = self.detect_protected_regions(frame_path)
                # Limit regions per frame to avoid too many detections
                all_regions.extend(regions[:3])
            except Exception as e:
                logger.warning(f"ROI detection failed for frame: {str(e)}")
                continue
        
        # Calculate union of all detected regions
        union = self.union_regions(all_regions)
        
        if not union:
            return None
        
        x, y, w, h = union
        # Return center of the union region
        return (x + w / 2.0, y + h / 2.0)
    
    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a single image with custom prompt
        
        Args:
            image_path: Path to image file
            prompt: Custom analysis prompt
            
        Returns:
            Analysis results
        """
        try:
            if not prompt:
                prompt = """
                Analyze this image and provide:
                1. Brief description of main content
                2. Key objects, people, or elements present
                3. Setting or context
                4. Notable activities or actions
                5. Overall mood or atmosphere
                
                Be concise but informative.
                """
            
            uploaded_file = genai.upload_file(path=image_path)
            
            response = self.model.generate_content(
                [uploaded_file, prompt],
                safety_settings=self.safety_settings
            )
            
            return {
                "analysis": response.text,
                "image_path": image_path,
                "timestamp": os.path.getctime(image_path) if os.path.exists(image_path) else None
            }
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            return {"error": str(e)}
        finally:
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass
