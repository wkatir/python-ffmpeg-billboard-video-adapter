"""
Campaign Adaptation Software
A Streamlit application for intelligent video adaptation to billboard and LED display formats
"""

import streamlit as st
import os
import tempfile
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("campaign-adapter")

# Import our custom modules
from src.config import Config
from src.formats import ALL_FORMATS, get_format_categories
from src.utils import ensure_dirs, validate_ffmpeg_installation, create_temp_file, write_zip, cleanup_old_files
from src.video_processor import VideoProcessor
from src.gemini_client import GeminiClient

def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Campaign Adaptation Software",
        page_icon="🧩",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Setup environment and configuration
    ensure_dirs()
    config = Config()
    
    # Clean up old temporary files (older than 24 hours)
    try:
        temp_cleaned = cleanup_old_files(config.TEMP_DIR, max_age_hours=24)
        output_cleaned = cleanup_old_files(config.OUTPUT_DIR, max_age_hours=48)
        if temp_cleaned > 0 or output_cleaned > 0:
            logger.info(f"Cleaned up {temp_cleaned} temp files and {output_cleaned} output files")
    except Exception as e:
        logger.warning(f"File cleanup failed: {str(e)}")
    
    # Header
    st.title("🧩 Campaign Adaptation Software")
    st.caption("FFmpeg + AI (Gemini) • Campaign adaptation to billboard formats • *VNNOX not included (yet)*")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Adaptation mode
        st.markdown("**Adaptation Modes**")
        mode = st.radio("Mode", options=["fit (pad)", "fill (crop)"], index=1)
        mode_key = "fit" if mode.startswith("fit") else "fill"
        
        blur_bg = st.toggle("Blur background (FIT mode only)", value=False)
        legibility = st.toggle("Enhance legibility (sharpen+contrast)", value=True)
        
        st.divider()
        st.markdown("**AI-Guided (Optional)**")
        ai_enabled = st.toggle("Enable AI-guided cropping (protect logos/text/faces)", value=False)
        sample_fps = st.slider("Sampling FPS (frames analyzed)", min_value=0.2, max_value=2.0, step=0.2, value=0.6)
        max_frames = st.slider("Max AI frames", 3, 20, 10)
        
        st.divider()
        st.markdown("**Export**")
        batch = st.toggle("Multi-format batch", value=True)
        
        # Format selection
        format_categories = get_format_categories()
        selected_profiles = []
        
        for category, formats in format_categories.items():
            with st.expander(f"📺 {category}", expanded=(category == "LED Displays")):
                for format_key in formats:
                    profile = ALL_FORMATS[format_key]
                    if st.checkbox(
                        f"{profile.key} ({profile.width}x{profile.height}@{profile.fps}fps)",
                        value=(format_key in ["LED_16x9_FHD", "LED_960x320"]),
                        key=f"format_{format_key}"
                    ):
                        selected_profiles.append(format_key)
        
        st.markdown("**Custom Format (Optional)**")
        custom_on = st.toggle("Add custom format", value=False)
        cW = st.number_input("Custom Width", min_value=64, value=1080, step=2, disabled=not custom_on)
        cH = st.number_input("Custom Height", min_value=64, value=1920, step=2, disabled=not custom_on)
        
        st.divider()
        
        # System info
        st.subheader("ℹ️ System")
        if validate_ffmpeg_installation():
            st.success("✅ FFmpeg available")
        else:
            st.error("❌ FFmpeg not found")
        
        api_key_available = bool(config.get_gemini_api_key())
        if api_key_available:
            st.success("🔑 API Key configured")
        else:
            st.warning("🔑 API Key required for AI")
            st.caption("Set GOOGLE_API_KEY environment variable")
    
    # Main content area
    st.subheader("📁 Upload Video")
    uploaded = st.file_uploader(
        "Formats: mp4, avi, mov, mkv, wmv, flv, webm, m4v", 
        type=config.SUPPORTED_FORMATS
    )
    
    if uploaded:
        size_mb = uploaded.size / (1024 * 1024)
        st.info(f"**{uploaded.name}** • {size_mb:.2f} MB")
        
        if size_mb > config.MAX_FILE_SIZE:
            st.error(f"File exceeds limit of {config.MAX_FILE_SIZE} MB.")
            st.stop()
        
        if not validate_ffmpeg_installation():
            st.error("FFmpeg not detected. Please install it and try again.")
            st.stop()
        
        # Save to temp file
        ext = Path(uploaded.name).suffix
        tmp_in = create_temp_file(ext)
        try:
            with open(tmp_in, "wb") as f:
                f.write(uploaded.read())
        except Exception as e:
            st.error(f"Failed to save uploaded file: {str(e)}")
            st.stop()
        
        # Get video info (for internal use only)
        vp = VideoProcessor()
        info = vp.get_video_info(tmp_in)
    
    st.divider()
    st.subheader("🎯 Target Format Selection")
    
    # Build target profiles list
    targets: List[Dict] = []
    if batch and selected_profiles:
        for k in selected_profiles:
            p = ALL_FORMATS[k]
            targets.append({
                "key": p.key, 
                "width": p.width, 
                "height": p.height, 
                "fps": p.fps
            })
    
    if custom_on:
        targets.append({
            "key": f"CUSTOM_{cW}x{cH}", 
            "width": int(cW), 
            "height": int(cH), 
            "fps": info.get("frame_rate", 30)
        })
    
    if not targets:
        st.warning("Select at least one target format.")
        st.stop()
    
    # ROI detection with AI (optional)
    roi_center = None
    if ai_enabled:
        try:
            with st.status("Initializing AI analysis...", expanded=True) as status:
                gc = GeminiClient()
                
                # Test connection first
                status.update(label="Testing Gemini API connection...")
                if not gc.test_connection():
                    st.error("❌ Cannot connect to Gemini API. Check your API key.")
                    st.stop()
                
                status.update(label="Extracting frames for analysis...")
                frames_dir = tempfile.mkdtemp()
                frames = vp.extract_frames(tmp_in, frames_dir, frame_rate=sample_fps, fmt="jpg")
                frames = frames[:max_frames]
                
                st.info(f"🔍 Extracted {len(frames)} frames for AI analysis")
                
                status.update(label="Analyzing frames with AI to detect logos/text/faces...")
                roi = gc.suggest_crop_center(frames)
                
                if roi:
                    roi_center = roi  # (cx, cy) relative
                    st.success(f"✅ AI detected important content at center: ({roi[0]:.2f}, {roi[1]:.2f})")
                    st.info("🎯 AI-guided cropping will protect detected elements")
                else:
                    st.info("ℹ️ AI analysis complete - no specific regions detected, using center crop")
                
                status.update(label="AI analysis complete!", state="complete")
                
        except Exception as e:
            st.error(f"❌ AI analysis failed: {str(e)}")
            st.info("🔄 Continuing with standard center cropping...")
            logger.error(f"AI analysis error: {e}")
        finally:
            try:
                shutil.rmtree(frames_dir, ignore_errors=True)
            except Exception:
                pass
    
    st.divider()
    
    # Processing buttons
    colA, colB = st.columns([1, 1])
    
    with colA:
        if st.button("🚀 Adapt (single / first selection)", use_container_width=True):
            t0 = targets[0]
            try:
                with st.spinner(f"Processing video to {t0['width']}x{t0['height']}..."):
                    out_path = vp.adapt_to_format(
                        tmp_in, t0["width"], t0["height"],
                        mode=mode_key,
                        blur_bg=blur_bg if mode_key == "fit" else False,
                        legibility_boost=legibility,
                        roi_center=roi_center,
                        fps=t0.get("fps")
                    )
                st.success("Ready. Download and preview:")
                st.download_button(
                    "📥 Download", 
                    data=open(out_path, "rb").read(),
                    file_name=os.path.basename(out_path), 
                    mime="video/mp4", 
                    use_container_width=True
                )
                try:
                    prev = vp.create_preview_clip(out_path, seconds=3)
                    st.video(prev)
                except Exception:
                    st.video(out_path)
            except Exception as e:
                st.error(f"❌ Video processing failed: {str(e)}")
                logger.error(f"Video processing error: {e}")
                st.info("💡 Possible solutions:")
                st.markdown("""
                - Check if your video file is corrupted
                - Try a different video format
                - Ensure FFmpeg is properly installed
                - Check the logs for detailed error information
                """)
    
    with colB:
        if st.button("📦 Export Batch (ZIP)", use_container_width=True):
            try:
                with st.spinner(f"Processing batch ({len(targets)} formats)..."):
                    outs = vp.batch_adapt(
                        tmp_in,
                        profiles=targets,
                        mode=mode_key,
                        blur_bg=blur_bg if mode_key == "fit" else False,
                        legibility_boost=legibility,
                        roi_center=roi_center,
                        fps_map={t["key"]: t.get("fps") for t in targets},
                    )
                zip_path = os.path.join(config.OUTPUT_DIR, f"{Path(uploaded.name).stem}__batch.zip")
                write_zip(outs, zip_path)
                st.success(f"Batch complete: {len(outs)} files")
                st.download_button(
                    "📥 Download ZIP", 
                    data=open(zip_path, "rb").read(),
                    file_name=Path(zip_path).name, 
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Batch processing failed: {str(e)}")
                logger.error(f"Batch processing error: {e}")
                st.info("💡 Some files may have been processed successfully. Check the output directory.")
    
    st.divider()
    st.subheader("🔎 QA Preview")
    try:
        thumb_src = vp.create_thumbnail(tmp_in)
        st.caption("Original frame (approx. 1s)")
        st.image(thumb_src, use_container_width=True)
    except Exception:
        st.info("Could not generate thumbnail.")
    
    st.caption("Tip: verify brand safe areas and legibility before publishing.")

if __name__ == "__main__":
    main()