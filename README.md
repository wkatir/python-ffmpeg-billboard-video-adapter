# 🎬 FFmpeg Billboard Video Adapter

A powerful Streamlit web application that combines FFmpeg video processing with Google Gemini AI for intelligent video analysis and conversion.

## ✨ Features

- **Video Format Conversion**: Convert between multiple video formats (MP4, AVI, MOV, MKV, etc.)
- **Quality Control**: Adjust video quality with predefined settings (low, medium, high, ultra)
- **AI-Powered Analysis**: Use Google Gemini AI to analyze video content and generate insights
- **Frame Extraction**: Extract frames from videos for detailed analysis
- **Thumbnail Generation**: Create video thumbnails automatically
- **Real-time Progress**: Track processing progress with visual indicators
- **User-Friendly Interface**: Intuitive Streamlit web interface
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## 🛠️ Tech Stack

- **Python**: 3.9+ (tested with 3.13)
- **Streamlit**: Interactive web application framework
- **FFmpeg**: Professional video processing engine
- **Google Gemini AI**: Advanced AI for video content analysis
- **FFmpeg-Python**: Python bindings for FFmpeg

## 📋 Prerequisites

- Python 3.9 or higher
- FFmpeg installed on your system
- Google Gemini API key
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

### Basic Video Processing

1. **Upload Video**: Click "Choose a video file" and select your video
2. **Configure Settings**: 
   - Choose output format (MP4, AVI, MOV, MKV)
   - Select quality level (low, medium, high, ultra)
   - Enable/disable AI analysis
3. **Process**: Click "🚀 Process Video" to start conversion
4. **Download**: Download the processed video when complete

### AI Analysis Features

When AI analysis is enabled, the application will:
- Extract key frames from your video
- Analyze content using Google Gemini AI
- Generate comprehensive summaries
- Identify objects, scenes, and activities
- Provide detailed insights about video content

### Quality Settings

- **Low**: 640x480, 500k video bitrate, 64k audio bitrate
- **Medium**: 1280x720, 1000k video bitrate, 128k audio bitrate  
- **High**: 1920x1080, 2000k video bitrate, 192k audio bitrate
- **Ultra**: 1920x1080, 4000k video bitrate, 320k audio bitrate

## 🏗️ Project Structure

```
.
├── app.py                  # Main Streamlit application
├── src/                    # Source code modules
│   ├── __init__.py        # Package initialization
│   ├── config.py          # Configuration management
│   ├── utils.py           # Utility functions
│   ├── video_processor.py # FFmpeg video processing
│   └── gemini_client.py   # Google Gemini AI integration
├── temp/                  # Temporary files (auto-created)
├── output/                # Output files (auto-created)
├── logs/                  # Application logs (auto-created)
├── .env.template          # Environment template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.template` to `.env` and configure:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
MAX_FILE_SIZE_MB=500
DEFAULT_OUTPUT_FORMAT=mp4
DEFAULT_QUALITY=high
LOG_LEVEL=INFO
```

### Application Settings

Settings can be configured in `src/config.py`:
- Supported video formats
- Quality presets
- File size limits
- Processing options

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

**Made with ❤️ using Python, FFmpeg, and Google Gemini AI**
