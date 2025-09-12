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
    
    # Enhanced Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Processing Settings")
        
        # Video Processing Options
        with st.expander("🎥 Video Settings", expanded=True):
            output_format = st.selectbox(
                "Output Format",
                ["mp4", "avi", "mov", "mkv"],
                index=0,
                help="Choose the output video format"
            )
            
            quality = st.select_slider(
                "Video Quality",
                options=["low", "medium", "high", "ultra"],
                value="high",
                help="Higher quality = larger file size"
            )
            
            # Show quality details
            quality_info = {
                "low": "640x480, 500k bitrate",
                "medium": "1280x720, 1M bitrate", 
                "high": "1920x1080, 2M bitrate",
                "ultra": "1920x1080, 4M bitrate"
            }
            st.caption(f"📊 {quality_info[quality]}")
        
        # AI Analysis Options
        with st.expander("🤖 AI Analysis", expanded=True):
            enable_ai_analysis = st.checkbox(
                "Enable Gemini AI Analysis",
                value=True,
                help="Analyze video content with Google Gemini AI"
            )
            
            if enable_ai_analysis:
                st.success("✨ AI analysis will provide:")
                st.markdown("""
                • Content description
                • Object detection
                • Scene analysis
                • Visual insights
                """)
            else:
                st.info("🔧 Basic processing only")
        
        st.divider()
        
        # Quick Info
        st.subheader("ℹ️ Quick Info")
        st.markdown("""
        **Supported Formats:**  
        MP4, AVI, MOV, MKV, WMV, FLV
        
        **Max File Size:**  
        500 MB per file
        
        **AI Features:**  
        Powered by Google Gemini
        """)
        
        # API Key Status
        config = Config()
        api_key_available = bool(config.get_gemini_api_key())
        
        if api_key_available:
            st.success("🔑 API Key Configured")
        else:
            st.warning("🔑 API Key Required")
            st.caption("Set GOOGLE_API_KEY environment variable")
    
    # Information section (moved to top)
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.subheader("🎬 About This Tool")
        st.markdown("""
        **Powerful video processing** with AI-powered analysis:
        
        • **FFmpeg Integration** - Industry-standard video processing
        • **Google Gemini AI** - Advanced content analysis  
        • **Multiple Formats** - Support for all major video formats
        • **Quality Control** - Choose from 4 quality presets
        """)
    
    with info_col2:
        st.subheader("✨ Key Features")
        st.markdown("""
        **Transform your videos with ease:**
        
        • Format conversion between popular video types
        • Quality optimization for different use cases  
        • AI-powered content analysis and insights
        • Real-time progress tracking during processing
        """)
    
    # Gemini AI Information (prominent display)
    if not enable_ai_analysis:
        st.info("💡 **Tip:** Enable AI Analysis in the sidebar to get detailed insights about your video content using Google Gemini AI!")
    else:
        st.success("🤖 **AI Analysis Enabled** - Your video will be analyzed by Google Gemini AI for content insights, object detection, and scene understanding.")
    
    st.divider()
    
    # Main processing area (moved below information)
    st.header("📁 Video Processing")
    
    # Upload section with better layout
    upload_col1, upload_col2 = st.columns([3, 2])
    
    with upload_col1:
        st.subheader("Upload Your Video")
        uploaded_file = st.file_uploader(
            "Choose a video file to process",
            type=['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv'],
            help="Supported formats: MP4, AVI, MOV, MKV, WMV, FLV"
        )
        
        if uploaded_file is not None:
            # Validate file
            if validate_file_type(uploaded_file):
                st.success(f"✅ File uploaded successfully: **{uploaded_file.name}**")
                
                # Display file info in a more compact way
                file_size_mb = uploaded_file.size / (1024*1024)
                st.info(f"📄 **{uploaded_file.name}** • {file_size_mb:.2f} MB • {uploaded_file.type}")
                
            else:
                st.error("❌ Invalid file type. Please upload a supported video format.")
    
    with upload_col2:
        if uploaded_file is not None and validate_file_type(uploaded_file):
            st.subheader("File Details")
            file_details = {
                "Filename": uploaded_file.name,
                "Size": f"{uploaded_file.size / (1024*1024):.2f} MB",
                "Type": uploaded_file.type
            }
            
            for key, value in file_details.items():
                st.metric(label=key, value=value)
    
    # Processing button section
    if uploaded_file is not None and validate_file_type(uploaded_file):
        st.divider()
        
        # Processing controls in a centered layout
        process_col1, process_col2, process_col3 = st.columns([1, 2, 1])
        
        with process_col2:
            st.subheader("🚀 Start Processing")
            
            # Show current settings
            settings_info = f"**Format:** {output_format.upper()} • **Quality:** {quality.title()}"
            if enable_ai_analysis:
                settings_info += " • **AI Analysis:** Enabled 🤖"
            else:
                settings_info += " • **AI Analysis:** Disabled"
            
            st.info(settings_info)
            
            if st.button("🚀 Process Video Now", type="primary", use_container_width=True):
                process_video(
                    uploaded_file, 
                    output_format, 
                    quality, 
                    enable_ai_analysis
                )

def process_video(uploaded_file, output_format: str, quality: str, enable_ai_analysis: bool):
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
            if enable_ai_analysis:
                status_text.text("🤖 Analyzing video with AI...")
                progress_bar.progress(75)
                
                try:
                    gemini_client = GeminiClient()  # Will get API key from config/environment
                    analysis_result = gemini_client.analyze_video(input_path)
                except Exception as e:
                    st.warning(f"⚠️ AI Analysis failed: {str(e)}")
                    logger.warning(f"AI Analysis failed: {str(e)}")
            
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