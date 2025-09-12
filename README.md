# 🧩 Campaign Adaptation Software

A powerful Streamlit web application for intelligent video adaptation to billboard and LED display formats, combining FFmpeg video processing with Google Gemini AI for smart content-aware cropping.

## ✨ Features

- **Billboard Format Adaptation**: Specialized profiles for LED displays and digital billboards
- **Intelligent Cropping**: AI-guided cropping that protects logos, text, and faces
- **Aspect Ratio Preservation**: FIT (pad/letterbox) and FILL (crop) modes
- **Blurred Background Extension**: Elegant background extension for FIT mode
- **Legibility Enhancement**: Automatic sharpening and contrast boost for billboard content
- **Batch Export**: Process multiple formats simultaneously with ZIP download
- **ROI Detection**: Google Gemini AI detects regions of interest to preserve
- **QA Preview**: Thumbnail and clip preview for quality assurance
- **Real-time Processing**: Live progress tracking and preview generation

## 🛠️ Tech Stack

- **Python**: 3.9+ (tested with 3.13)
- **Streamlit**: Interactive web application framework
- **FFmpeg**: Professional video processing engine
- **Google Gemini AI**: AI-powered ROI detection and content analysis
- **FFmpeg-Python**: Python bindings for FFmpeg
- **imageio-ffmpeg**: Bundled FFmpeg executable

## 📋 Prerequisites

- Python 3.9 or higher
- FFmpeg installed on your system (or use bundled imageio-ffmpeg)
- Google Gemini API key (optional, for AI-guided features)
- Windows PowerShell (for Windows users)

### Installing FFmpeg

**Windows:**
1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract and add to your system PATH
3. Verify installation: `ffmpeg -version`

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

## 🚀 Quick Start

### 1. Clone and Setup Environment

```powershell
# Clone the repository
git clone <repository-url>
cd python-ffmpeg-billboard-video-adapter

# Create virtual environment
python -m venv .venv

# Activate virtual environment (PowerShell)
.\.venv\Scripts\Activate.ps1

# If activation is blocked, run:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

### 2. Install Dependencies

```powershell
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install streamlit google-generativeai python-dotenv ffmpeg-python
```

### 3. Configure API Key

1. Get your Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Copy `.env.template` to `.env`:
   ```powershell
   copy .env.template .env
   ```
3. Edit `.env` and add your API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

### 4. Run the Application

```powershell
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## 📖 Usage Guide

### Campaign Video Adaptation

1. **Upload Video**: Select your campaign video (MP4, AVI, MOV, MKV, WMV, FLV, WEBM, M4V)
2. **Configure Adaptation Settings**:
   - **Mode**: Choose FIT (pad/letterbox) or FILL (crop to fill)
   - **Blur Background**: Enable elegant background extension for FIT mode
   - **Legibility Boost**: Enhance sharpening and contrast for billboard viewing
3. **Select Target Formats**:
   - **LED Displays**: Standard LED format profiles (16:9, 9:16, 4:3, ultra-wide)
   - **Billboards**: Digital billboard format profiles
   - **Custom**: Define your own width x height format
4. **AI-Guided Cropping** (Optional):
   - Enable AI analysis to detect and protect logos, text, and faces
   - Adjust sampling rate and frame analysis limits
5. **Process**:
   - **Single**: Adapt to first selected format
   - **Batch**: Export all selected formats as ZIP
6. **Quality Assurance**: Preview thumbnail and verify safe areas

### Adaptation Modes

- **FIT Mode**: Preserves original aspect ratio, adds padding (letterbox/pillarbox)
  - Optional blurred background extension for aesthetic appeal
- **FILL Mode**: Crops video to fill target aspect ratio completely
  - AI-guided center positioning to protect important content

### Built-in Format Profiles

**LED Displays:**
- LED_16x9_FHD: 1920x1080@30fps (Full HD landscape)
- LED_9x16_FHD: 1080x1920@30fps (Full HD portrait)
- LED_4x3_XGA: 1024x768@30fps (Traditional aspect ratio)
- LED_960x320: 960x320@30fps (Ultra-wide strip displays)
- LED_256x128: 256x128@25fps (Low-res matrix displays)

**Digital Billboards:**
- BILLBOARD_14x48: 1680x480@30fps (Standard billboard)
- BILLBOARD_12x24: 1440x720@30fps (Junior billboard)
- BILLBOARD_6x12: 720x360@30fps (Poster billboard)

## 🏗️ Project Structure

```
.
├── app.py                  # Main Campaign Adaptation application
├── src/                    # Source code modules
│   ├── __init__.py        # Package initialization
│   ├── config.py          # Configuration management
│   ├── formats.py         # Billboard/LED format profiles
│   ├── utils.py           # Utility functions
│   ├── video_processor.py # Specialized video adaptation engine
│   └── gemini_client.py   # ROI detection with Google Gemini AI
├── temp/                  # Temporary files (auto-created)
├── output/                # Adapted videos and ZIP exports (auto-created)
├── logs/                  # Application logs (auto-created)
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This documentation
```

## ⚙️ Configuration

### Environment Variables

Set the following environment variables:

```bash
# Required for AI-guided features (optional)
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional customizations
MAX_FILE_SIZE_MB=500
TEMP_DIR=./temp
OUTPUT_DIR=./output
LOG_DIR=./logs
```

### Application Settings

Settings can be configured in `src/config.py`:
- Billboard and LED format profiles
- Adaptation modes and parameters
- File size limits
- AI analysis settings

## 🔧 Advanced Usage

### Custom Quality Settings

Modify quality settings in `src/config.py`:

```python
QUALITY_SETTINGS = {
    "custom": {
        "video_bitrate": "3000k",
        "audio_bitrate": "256k",
        "scale": "1920:1080",
        "fps": 30
    }
}
```

### Batch Processing

The application supports processing multiple files by uploading them sequentially.

### API Integration

The Gemini client can be used programmatically:

```python
from src.gemini_client import GeminiClient

client = GeminiClient("your_api_key")
analysis = client.analyze_video("path/to/video.mp4")
```

## 🐛 Troubleshooting

### Common Issues

1. **FFmpeg not found**: Ensure FFmpeg is installed and in your PATH
2. **API key errors**: Verify your Gemini API key is correct and has proper permissions
3. **Memory issues**: Large videos may require more system memory
4. **Permission errors**: Ensure write permissions for temp and output directories

### Logging

Check logs in the `logs/` directory for detailed error information:
```powershell
type logs\app.log
```

### System Requirements

- **RAM**: 4GB minimum, 8GB+ recommended for large videos
- **Storage**: Temporary space equal to 2-3x your video file size
- **CPU**: Multi-core processor recommended for faster processing

## 📝 Development

### Adding New Features

1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes in appropriate modules
3. Add tests and documentation
4. Submit pull request

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Include logging for important operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **FFmpeg**: The backbone of video processing
- **Google Gemini AI**: Powering intelligent video analysis
- **Streamlit**: Making web apps simple and beautiful
- **Python Community**: For excellent libraries and tools

## 📞 Support

For support and questions:
1. Check the troubleshooting section
2. Review application logs
3. Create an issue on GitHub
4. Contact the development team

---

**Made with ❤️ for the digital advertising industry using Python, FFmpeg, and Google Gemini AI**
