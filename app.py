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
from src.formats import STANDARD_FORMATS, ALL_FORMATS, get_format_categories, create_custom_format
from src.utils import ensure_dirs, validate_ffmpeg_installation, create_temp_file, cleanup_temp_files, write_zip, validate_file_type
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
    
    # Header
    st.title("🧩 Campaign Adaptation Software")
    st.caption("FFmpeg + IA (Gemini) • Adaptación de campañas a formatos de valla • *VNNOX no incluido (aún)*")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Ajustes")
        
        # Adaptation mode
        st.markdown("**Modos de adaptación**")
        mode = st.radio("Modo", options=["fit (pad)", "fill (crop)"], index=1)
        mode_key = "fit" if mode.startswith("fit") else "fill"
        
        blur_bg = st.toggle("Fondo blur (solo FIT)", value=False)
        legibility = st.toggle("Mejorar legibilidad (sharpen+contraste)", value=True)
        
        st.divider()
        st.markdown("**IA guiada (opcional)**")
        ai_enabled = st.toggle("Activar recorte guiado por IA (proteger logos/texto/rostros)", value=False)
        sample_fps = st.slider("FPS de muestreo (frames analizados)", min_value=0.2, max_value=2.0, step=0.2, value=0.6)
        max_frames = st.slider("Máx. frames IA", 3, 20, 10)
        
        st.divider()
        st.markdown("**Exportación**")
        batch = st.toggle("Batch multi-formato", value=True)
        
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
        
        st.markdown("**Formato Custom (opcional)**")
        custom_on = st.toggle("Agregar un formato custom", value=False)
        cW = st.number_input("Custom Width", min_value=64, value=1080, step=2, disabled=not custom_on)
        cH = st.number_input("Custom Height", min_value=64, value=1920, step=2, disabled=not custom_on)
        
        st.divider()
        
        # System info
        st.subheader("ℹ️ Sistema")
        if validate_ffmpeg_installation():
            st.success("✅ FFmpeg disponible")
        else:
            st.error("❌ FFmpeg no encontrado")
        
        api_key_available = bool(config.get_gemini_api_key())
        if api_key_available:
            st.success("🔑 API Key configurada")
        else:
            st.warning("🔑 API Key requerida para IA")
            st.caption("Set GOOGLE_API_KEY environment variable")
    
    # Main content area
    st.subheader("📁 Subir video")
    uploaded = st.file_uploader(
        "Formatos: mp4, avi, mov, mkv, wmv, flv, webm, m4v", 
        type=config.SUPPORTED_FORMATS
    )
    
    if uploaded:
        size_mb = uploaded.size / (1024 * 1024)
        st.info(f"**{uploaded.name}** • {size_mb:.2f} MB")
        
        if size_mb > config.MAX_FILE_SIZE:
            st.error(f"El archivo supera el límite de {config.MAX_FILE_SIZE} MB.")
            st.stop()
        
        if not validate_ffmpeg_installation():
            st.error("FFmpeg no detectado. Instálalo y vuelve a intentar.")
            st.stop()
        
        # Save to temp file
        ext = Path(uploaded.name).suffix
        tmp_in = create_temp_file(ext)
        with open(tmp_in, "wb") as f:
            f.write(uploaded.read())
        
        # Get video info
        vp = VideoProcessor()
        info = vp.get_video_info(tmp_in)
        
        # Display video info
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Resolución", f"{info.get('width','?')}×{info.get('height','?')}")
        c2.metric("Duración", info.get("duration_formatted","?"))
        c3.metric("FPS", f"{info.get('frame_rate',0):.2f}")
        c4.metric("Codec", info.get("video_codec","?"))
    
    st.divider()
        st.subheader("🎯 Selección de formatos destino")
        
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
            st.warning("Selecciona al menos un formato destino.")
            st.stop()
        
        # ROI detection with AI (optional)
        roi_center = None
        if ai_enabled:
            try:
                gc = GeminiClient()
                frames_dir = tempfile.mkdtemp()
                frames = vp.extract_frames(tmp_in, frames_dir, frame_rate=sample_fps, fmt="jpg")
                frames = frames[:max_frames]
                with st.status("Analizando frames con IA para proteger logos/texto/rostros...", expanded=False):
                    roi = gc.suggest_crop_center(frames)
                roi_center = roi  # (cx, cy) relative
            except Exception as e:
                st.warning(f"IA no disponible: {e}")
            finally:
                try:
                    shutil.rmtree(frames_dir, ignore_errors=True)
                except Exception:
                    pass
        
        st.divider()
        
        # Processing buttons
        colA, colB = st.columns([1, 1])
        
        with colA:
            if st.button("🚀 Adaptar (single / primera selección)", use_container_width=True):
                t0 = targets[0]
                out_path = vp.adapt_to_format(
                    tmp_in, t0["width"], t0["height"],
                    mode=mode_key,
                    blur_bg=blur_bg if mode_key == "fit" else False,
                    legibility_boost=legibility,
                    roi_center=roi_center,
                    fps=t0.get("fps")
                )
                st.success("Listo. Descarga y previsualiza:")
                st.download_button(
                    "📥 Descargar", 
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
        
        with colB:
            if st.button("📦 Exportar Batch (ZIP)", use_container_width=True):
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
                st.success(f"Batch completo: {len(outs)} archivos")
                st.download_button(
                    "📥 Descargar ZIP", 
                    data=open(zip_path, "rb").read(),
                    file_name=Path(zip_path).name, 
                    use_container_width=True
                )
        
        st.divider()
        st.subheader("🔎 QA Preview")
        try:
            thumb_src = vp.create_thumbnail(tmp_in)
            st.caption("Frame original (aprox. 1s)")
            st.image(thumb_src, use_column_width=True)
        except Exception:
            st.info("No se pudo generar thumbnail.")
        
        st.caption("Consejo: verifica safe areas de marca y legibilidad antes de publicar.")

if __name__ == "__main__":
    main()