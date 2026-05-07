# 🎬 Media Transcoder

A full-stack media conversion engine built with **FastAPI** and **yt-dlp** that lets you download YouTube videos or extract MP3 audio directly from your browser.

> ⚠️ **Disclaimer:** This tool is intended for **personal and educational use only**. Downloading copyrighted content may violate YouTube's Terms of Service. Only download content you own or have permission to download.

---

## ✨ Features

- 🎥 Download YouTube videos in **MP4** format (360p, 480p, 720p)
- 🎵 Extract audio as **MP3** (128kbps, 192kbps, 256kbps) using FFmpeg
- 📊 **Real-time progress bar** that updates every second
- 💾 **Browser Save dialog** — user chooses where to save the file
- 🏗️ Clean **OOP architecture** using Abstract Base Classes
- ⚡ **Asynchronous background downloads** using Python threads
- 🖥️ Minimal dark-themed **responsive UI**
- 🛡️ **Error handling** with clear user feedback

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Downloading | yt-dlp |
| Audio Conversion | FFmpeg |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Server | Uvicorn (ASGI) |
| Templates | Jinja2 |

---

## 📁 Project Structure

```
media-transcoder/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI routes and endpoints
│   └── models.py        # OOP classes (MediaDownloader, Managers, etc.)
├── static/
│   ├── style.css        # Dark theme UI styling
│   └── script.js        # Frontend logic and API calls
├── templates/
│   └── index.html       # Main HTML page
├── downloads/           # Downloaded files folder (created automatically)
├── run.py              # Application entry point
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- FFmpeg (required for audio conversion)
- Windows, macOS, or Linux

### Installation

1. **Clone or download the project:**
   ```bash
   cd media-transcoder
   ```

2. **Create a Python virtual environment:**
   ```bash
   python -m venv env
   ```

3. **Activate the virtual environment:**
   
   **Windows:**
   ```bash
   env\Scripts\activate
   ```
   
   **macOS/Linux:**
   ```bash
   source env/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install FFmpeg:**
   
   **Windows (using Chocolatey):**
   ```bash
   choco install ffmpeg
   ```
   
   **macOS (using Homebrew):**
   ```bash
   brew install ffmpeg
   ```
   
   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt-get install ffmpeg
   ```

### Running the Application

```bash
python run.py
```

The application will start on `http://127.0.0.1:8000`

Open your browser and navigate to the URL to start downloading!

---

## 📚 API Endpoints

### `GET /`
Serves the main HTML page.

### `POST /download`
Start a new download job.

**Request body:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "media_type": "video",
  "quality": "720p"
}
```

**Response:**
```json
{
  "job_id": "uuid-string"
}
```

### `GET /status/{job_id}`
Get the status of a download job.

**Response:**
```json
{
  "status": "downloading|done|error",
  "progress": 0-100,
  "filename": "/path/to/file.mp4",
  "error": null
}
```

### `GET /file/{job_id}`
Download the completed file (only works when status is "done").

### `DELETE /job/{job_id}`
Delete a job and clean up its files.

---

## 🎨 Customization

### Change Download Quality

Edit the quality buttons in [templates/index.html](templates/index.html) or modify the quality maps in [app/models.py](app/models.py).

### Change Server Port

Edit [run.py](run.py):
```python
uvicorn.run(..., port=8080)  # Change 8000 to your desired port
```

### Change Output Directory

Edit [app/models.py](app/models.py):
```python
def __init__(self, url: str, quality: str = "720p", output_dir: str = "downloads"):
```

---

## 🐛 Troubleshooting

### "FFmpeg not found"
- Make sure FFmpeg is installed and added to your system PATH
- Restart your terminal after installing FFmpeg

### "Module not found" errors
- Ensure your virtual environment is activated
- Run `pip install -r requirements.txt` again

### Downloads not starting
- Check the browser console (F12) for errors
- Verify the URL is valid and accessible
- Check that the backend server is running

### Files not downloading from browser
- Some browsers may have download restrictions
- Try a different browser or check browser download settings
- Check file permissions in the downloads folder

---

## 📝 Code Quality

The codebase follows these principles:
- **Clean Code**: Clear naming, proper documentation
- **OOP Design**: Abstract base classes and inheritance
- **Error Handling**: Try-catch blocks and user-friendly messages
- **Separation of Concerns**: Frontend/Backend separation

---

## 📄 License

This project is provided as-is for educational and personal use.

---

## 👥 Contributors

- **Elmehdi Elmellouki**
- **Younes Amazzal**

---

## ❓ Support

For issues or questions, please open an issue in the repository or contact the maintainers.

---

## ⚙️ Setup & Installation

### Prerequisites

Make sure these are installed on your system:

- **Python 3.11+** → [python.org/downloads](https://python.org/downloads) — ✅ check "Add to PATH" during install
- **FFmpeg** → install via winget:
  ```cmd
  winget install Gyan.FFmpeg
  ```

### Installation Steps

**1. Clone the repository**
```cmd
git clone https://github.com/yourusername/media-transcoder.git
cd media-transcoder
```

**2. Create and activate virtual environment**
```cmd
python -m venv env

# Windows CMD
env\Scripts\activate.bat

# Windows PowerShell
env\Scripts\Activate.ps1
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**3. Install dependencies**
```cmd
pip install fastapi uvicorn yt-dlp python-dotenv jinja2 aiofiles
```

**4. Run the server**
```cmd
uvicorn app.main:app --reload --port 8000
```

**5. Open in browser**
```
http://localhost:8000
```

---

## 🚀 Usage

1. Paste any YouTube URL into the input field
2. Choose **Video (MP4)** or **Audio (MP3)**
3. Click **Download**
4. Watch the real-time progress bar
5. Click **💾 Save File** when done — your browser's Save dialog will open

---

## 🏗️ OOP Architecture

```
MediaDownloader (Abstract Base Class)
├── VideoDownloader     → MP4 downloads
└── AudioDownloader     → MP3 extraction via FFmpeg

DownloadManager (Factory Pattern)
├── create_job()        → picks the right downloader
├── start_job()         → runs download in background thread
├── get_status()        → returns progress and status
└── delete_job()        → cleans up files after download
```

---

## 🌐 API Endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/` | Serves the main HTML page |
| POST | `/download` | Creates and starts a download job |
| GET | `/status/{job_id}` | Returns current progress and status |
| GET | `/file/{job_id}` | Sends the finished file to the browser |
| DELETE | `/job/{job_id}` | Deletes the job and its file |

---

## 🔮 Planned Features

### v2.0
- [ ] 📋 **Download History** — SQLite database to track all past downloads
- [ ] 🔍 **YouTube API Preview** — show video thumbnail, title and view count before downloading
- [✅ ] 📂 **Custom Output Path** — let the user choose a default save folder
- [✅ ] 🎚️ **Quality Selector** — choose video resolution (720p, 480p, 360p)
- [✅ ] 🎚️ **Quality Selector** — choose audio resolution (256kbps, 190Kbps, 128Kbps)

### v3.0
- [ ] 📦 **Batch Downloads** — paste multiple URLs and download them all at once
- [ ] 🎬 **Playlist Support** — download entire YouTube playlists
- [ ] 🌐 **Multi-Platform Support** — support for Vimeo, SoundCloud, Twitter/X
- [ ] 🔔 **Desktop Notifications** — notify the user when a download finishes
- [ ] 📊 **Download Queue Dashboard** — manage multiple concurrent downloads

### v4.0
- [ ] 🔐 **User Authentication** — login system with personal download history
- [ ] ☁️ **Cloud Deployment** — deploy to Railway or Render for public access
- [ ] 📱 **Mobile-Responsive UI** — optimized layout for phones and tablets
- [ ] 🌍 **Multi-Language Support** — French, Arabic, English UI

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first.

---

## 👨‍💻 Author

Built by ***Elmehdi Elmellouki*** — CS student at Cadi Ayyad University, Marrakech 🇲🇦

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Elmehdi%20Elmellouki-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/elmehdi-elmellouki-963552331/)