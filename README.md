## Python Streamlit App

Simple Streamlit project with a clean virtual environment setup and pinned dependencies. The main entry file is `app.py`.

### Tech stack
- **Python**: 3.13 (works with 3.9+)
- **Streamlit**: Interactive web apps for data
- **Pandas**: Data handling
- Other pinned libraries in `requirements.txt`

### Prerequisites
- Python installed and available as `python` or `py` on your system PATH
- Windows PowerShell (instructions below use PowerShell)

### 1) Create and activate a virtual environment (recommended)
```powershell
# From the project root
python -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# If activation is blocked by policy, run this and try again:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

To deactivate later:
```powershell
deactivate
```

### 2) Install dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Run the app
```powershell
streamlit run app.py
```

You can also try Streamlit’s demo:
```powershell
streamlit hello
```

### Project layout
```
.
├─ app.py                # Main Streamlit app (entry point)
├─ requirements.txt      # Pinned dependencies
└─ .gitignore            # Ignores .venv, caches, etc.
```
