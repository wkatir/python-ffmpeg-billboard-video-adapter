"""
FFmpeg Billboard Video Adapter with Google Gemini AI
A Streamlit application for video processing and AI-powered analysis
"""

import streamlit as st
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our custom modules
from src.video_processor import VideoProcessor
from src.gemini_client import GeminiClient
from src.config import Config
from src.utils import setup_environment, validate_file_type

def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="FFmpeg Billboard Video Adapter",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Setup environment and configuration
    setup_environment()
    config = Config()
    
    # Header
    st.title("🎬 FFmpeg Billboard Video Adapter")
    st.markdown("Transform your videos with AI-powered analysis using FFmpeg and Google Gemini")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Gemini API Key input
        api_key = st.text_input(
            "Google Gemini API Key",
            type="password",
            help="Enter your Google Gemini API key"
        )
        
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            st.success("✅ API Key configured")
        else:
            st.warning("⚠️ Please enter your Gemini API key to enable AI features")
        
        st.divider()
        
        # Processing options
        st.subheader("Processing Options")
        
        output_format = st.selectbox(
            "Output Format",
            ["mp4", "avi", "mov", "mkv"],
            index=0
        )
        
        quality = st.select_slider(
            "Video Quality",
            options=["low", "medium", "high", "ultra"],
            value="high"
        )
        
        enable_ai_analysis = st.checkbox(
            "Enable AI Analysis",
            value=True,
            help="Use Google Gemini to analyze video content"
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 Upload Video")
        
        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv'],
            help="Upload a video file for processing"
        )
        
        if uploaded_file is not None:
            # Validate file
            if validate_file_type(uploaded_file):
                st.success(f"✅ File uploaded: {uploaded_file.name}")
                
                # Display file info
                file_details = {
                    "Filename": uploaded_file.name,
                    "File size": f"{uploaded_file.size / (1024*1024):.2f} MB",
                    "File type": uploaded_file.type
                }
                
                st.json(file_details)
                
                # Process button
                if st.button("🚀 Process Video", type="primary"):
                    process_video(
                        uploaded_file, 
                        output_format, 
                        quality, 
                        enable_ai_analysis,
                        api_key
                    )
            else:
                st.error("❌ Invalid file type. Please upload a supported video format.")
    
    with col2:
        st.header("ℹ️ About")
        st.markdown("""
        This application combines the power of:
        
        - **FFmpeg**: Industry-standard video processing
        - **Google Gemini AI**: Advanced video content analysis
        - **Streamlit**: Interactive web interface
        
        ### Features:
        - Video format conversion
        - Quality adjustment
        - AI-powered content analysis
        - Batch processing support
        - Real-time progress tracking
        """)
        
        # System info
        st.subheader("System Status")
        
        # Check FFmpeg availability
        try:
            import ffmpeg
            st.success("✅ FFmpeg available")
        except Exception as e:
            st.error(f"❌ FFmpeg error: {str(e)}")
        
        # Check Gemini API
        if api_key:
            try:
                gemini_client = GeminiClient(api_key)
                if gemini_client.test_connection():
                    st.success("✅ Gemini AI connected")
                else:
                    st.error("❌ Gemini AI connection failed")
            except Exception as e:
                st.error(f"❌ Gemini AI error: {str(e)}")
        else:
            st.info("ℹ️ Gemini AI not configured")

def process_video(uploaded_file, output_format: str, quality: str, enable_ai_analysis: bool, api_key: Optional[str]):
    """Process the uploaded video file"""
    
    try:
        with st.spinner("Processing video..."):
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_input:
                tmp_input.write(uploaded_file.read())
                input_path = tmp_input.name
            
            # Initialize video processor
            video_processor = VideoProcessor()
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Process video
            status_text.text("🔄 Converting video format...")
            progress_bar.progress(25)
            
            output_path = video_processor.convert_video(
                input_path=input_path,
                output_format=output_format,
                quality=quality
            )
            
            progress_bar.progress(50)
            
            # AI Analysis if enabled
            analysis_result = None
            if enable_ai_analysis and api_key:
                status_text.text("🤖 Analyzing video with AI...")
                progress_bar.progress(75)
                
                gemini_client = GeminiClient(api_key)
                analysis_result = gemini_client.analyze_video(input_path)
            
            progress_bar.progress(100)
            status_text.text("✅ Processing complete!")
            
            # Display results
            display_results(output_path, analysis_result)
            
            # Cleanup
            cleanup_temp_files([input_path])
            
    except Exception as e:
        st.error(f"❌ Error processing video: {str(e)}")
        logger.error(f"Video processing error: {str(e)}")

def display_results(output_path: str, analysis_result: Optional[Dict[str, Any]]):
    """Display processing results"""
    
    st.header("📊 Results")
    
    # Video download
    if os.path.exists(output_path):
        with open(output_path, "rb") as file:
            st.download_button(
                label="📥 Download Processed Video",
                data=file.read(),
                file_name=os.path.basename(output_path),
                mime="video/mp4"
            )
    
    # AI Analysis results
    if analysis_result:
        st.subheader("🤖 AI Analysis")
        
        # Display analysis in tabs
        tab1, tab2, tab3 = st.tabs(["Summary", "Details", "Raw Data"])
        
        with tab1:
            if "summary" in analysis_result:
                st.write(analysis_result["summary"])
        
        with tab2:
            if "details" in analysis_result:
                for key, value in analysis_result["details"].items():
                    st.write(f"**{key}**: {value}")
        
        with tab3:
            st.json(analysis_result)

def cleanup_temp_files(file_paths: list):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {str(e)}")

if __name__ == "__main__":
    main()