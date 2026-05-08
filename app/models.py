from pathlib import Path
import yt_dlp
import os
import threading
import time
from abc import ABC, abstractmethod


class MediaDownloader(ABC):
    """Base class for media downloading with multi-strategy YouTube bypass."""
    
    def __init__(self, url: str, output_dir: str):
        self.url = url
        self.output_dir = str(output_dir)
        self.progress = 0
        self.status = "pending"
        self.filename = None
        self.error = None
        
        os.makedirs(self.output_dir, exist_ok=True)

    @abstractmethod
    def get_options(self) -> dict:
        pass
    
    def _build_strategy(self, attempt: int) -> dict:
        """Build yt-dlp options with rotating bypass strategies."""
        
        po_token = os.getenv("YOUTUBE_PO_TOKEN", "")
        visitor_data = os.getenv("YOUTUBE_VISITOR_DATA", "")
        cookie_path = Path("cookies.txt")
        has_cookies = cookie_path.exists()
        
        # Strategy rotation based on attempt number
        strategies = []
        
        # Strategy 0: Web client + PO token (best quality, requires env vars)
        if po_token:
            strategies.append({
                "extractor_args": {
                    "youtube": {
                        "player_client": ["web"],
                        "po_token": [po_token],
                        "visitor_data": [visitor_data],
                        "player_skip": ["configs", "js"],
                    }
                }
            })
        
        # Strategy 1: TV embedded (no auth, medium quality, bypasses most bot checks)
        strategies.append({
            "extractor_args": {
                "youtube": {
                    "player_client": ["tv_embedded"],
                    "player_skip": ["webpage", "configs", "js"],
                }
            }
        })
        
        # Strategy 2: Android client (mobile app API, different IP reputation)
        strategies.append({
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"],
                    "player_skip": ["configs", "js"],
                }
            }
        })
        
        # Strategy 3: iOS client
        strategies.append({
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios"],
                    "player_skip": ["configs", "js"],
                }
            }
        })
        
        # Strategy 4: Web with cookies (if cookies.txt exists)
        if has_cookies:
            strategies.append({
                "cookiefile": str(cookie_path),
                "extractor_args": {
                    "youtube": {
                        "player_client": ["web"],
                        "player_skip": ["configs", "js"],
                    }
                }
            })
        
        # Pick strategy based on attempt (cycle through)
        strategy = strategies[attempt % len(strategies)] if strategies else {}
        
        base = {
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "retries": 10,
            "fragment_retries": 10,
            "file_access_retries": 5,
            "extractor_retries": 5,
            "geo_bypass": True,
            "skip_unavailable_fragments": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }
        proxy = os.getenv("PROXY_URL", "")
        if proxy:
             base["proxy"] = proxy
        
        base.update(strategy)
        return base
    
    def _progress_hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 1)
            downloaded = d.get("downloaded_bytes", 0)
            self.progress = int(downloaded / total * 100) if total > 0 else 0
            self.status = "downloading"
        elif d["status"] == "finished":
            self.progress = 99
            self.status = "downloading"

    def _postprocessor_hook(self, d):
        if d["status"] == "finished":
            self.progress = 100
            self.status = "done"
            self.filename = d["info_dict"].get("filepath") or d.get("filepath")

    def download(self):
        max_retries = 4
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait = 3 * attempt
                    self.status = "pending"
                    time.sleep(wait)
                
                opts = {**self._build_strategy(attempt), **self.get_options()}
                opts["progress_hooks"] = [self._progress_hook]
                opts["postprocessor_hooks"] = [self._postprocessor_hook]
                
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(self.url, download=True)
                    if not self.filename and info:
                        self.filename = ydl.prepare_filename(info)
                        self.progress = 100
                        self.status = "done"
                    return
                    
            except Exception as e:
                error_msg = str(e).lower()
                self.status = "error"
                
                # Check if we should try next strategy
                is_recoverable = any(k in error_msg for k in [
                    "bot", "sign in", "player response", "innertube",
                    "unable to extract", "403", "429", "timeout"
                ])
                
                if attempt < max_retries - 1 and is_recoverable:
                    continue
                
                self.error = self._format_error(error_msg, str(e))
                break
    
    def _format_error(self, error_msg: str, full: str) -> str:
        if "bot" in error_msg or "sign in" in error_msg:
            return "YouTube blocked this request. Try: 1) Add PO_TOKEN env var, 2) Upload cookies.txt, or 3) Use a proxy."
        if "403" in error_msg:
            return "Access denied by YouTube. Try again in 10 minutes or use a different video."
        if "not available" in error_msg:
            return "Video unavailable (private, deleted, or region-blocked)."
        if "ffmpeg" in error_msg:
            return "Server missing FFmpeg. Audio conversion failed."
        return f"Error: {full[:150]}"


class VideoDownloader(MediaDownloader):
    def __init__(self, url: str, quality: str = "720p", output_dir: str = "downloads"):
        super().__init__(url, output_dir)
        self.quality = quality

    def get_options(self) -> dict:
        quality_map = {
            "360p": "best[height<=360]",
            "480p": "best[height<=480]",
            "720p": "best[height<=720]",
        }
        return {
            "format": quality_map.get(self.quality, "best"),
            "outtmpl": os.path.join(self.output_dir, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
        }


class AudioDownloader(MediaDownloader):
    def __init__(self, url: str, quality: str = "192kbps", output_dir: str = "downloads"):
        super().__init__(url, output_dir)
        self.quality = quality

    def get_options(self) -> dict:
        quality_map = {
            "128kbps": "128",
            "192kbps": "192",
            "256kbps": "256",
        }
        return {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(self.output_dir, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality_map.get(self.quality, "192"),
            }],
        }


class DownloadManager:
    def __init__(self):
        self.jobs: dict[str, MediaDownloader] = {}

    def create_job(self, job_id: str, url: str, media_type: str, quality: str = "720p") -> MediaDownloader:
        if media_type == "audio":
            downloader = AudioDownloader(url, quality)
        else:
            downloader = VideoDownloader(url, quality)
        self.jobs[job_id] = downloader
        return downloader

    def start_job(self, job_id: str):
        downloader = self.jobs.get(job_id)
        if not downloader:
            return
        thread = threading.Thread(target=downloader.download, daemon=True)
        thread.start()

    def get_status(self, job_id: str) -> dict:
        job = self.jobs.get(job_id)
        if not job:
            return {"status": "not_found", "progress": 0}
        return {
            "status": job.status,
            "progress": job.progress,
            "filename": job.filename,
            "error": job.error
        }

    def delete_job(self, job_id: str):
        job = self.jobs.get(job_id)
        if job and job.filename and os.path.exists(job.filename):
            try:
                os.remove(job.filename)
            except OSError:
                pass
        self.jobs.pop(job_id, None)


manager = DownloadManager()