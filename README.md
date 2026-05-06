# 🎬 Media Transcoder

A full-stack media conversion engine built with **FastAPI** and **yt-dlp** that lets you download YouTube videos or extract MP3 audio directly from your browser.

> ⚠️ **Disclaimer:** This tool is intended for **personal and educational use only**. Downloading copyrighted content may violate YouTube's Terms of Service. Only download content you own or have permission to download.

---

## ✨ Features

- 🎥 Download YouTube videos in **MP4** format
- 🎵 Extract audio as **MP3** (192kbps) using FFmpeg
- 📊 **Real-time progress bar** that updates every second
- 💾 **Browser Save dialog** — user chooses where to save the file
- 🏗️ Clean **OOP architecture** using Abstract Base Classes and Factory Pattern
- ⚡ **Asynchronous background downloads** using Python threads
- 🖥️ Minimal dark-themed **responsive UI**

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
│   ├── main.py          # FastAPI routes
│   └── models.py        # OOP classes (MediaDownloader, VideoDownloader, AudioDownloader, DownloadManager)
├── static/
│   ├── style.css        # Dark theme UI
│   └── script.js        # Progress bar + fetch logic
├── templates/
│   └── index.html       # Main page
├── downloads/           # Temporary download folder
├── requirements.txt
└── README.md
```

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
- [ ] 📂 **Custom Output Path** — let the user choose a default save folder
- [ ] 🎚️ **Quality Selector** — choose video resolution (1080p, 720p, 480p)

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

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

Built by ***Elmehdi Elmellouki*** — CS student at Cadi Ayyad University, Marrakech 🇲🇦

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Elmehdi%20Elmellouki-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/elmehdi-elmellouki-963552331/)