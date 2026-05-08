from pathlib import Path
import yt_dlp
import os
import threading
import time
import logging
from abc import ABC, abstractmethod

# Enable logging so you can see yt-dlp output in Render logs
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MediaDownloader(ABC):
    
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
    
    def _base_options(self) -> dict:
        """Base options with forced IPv4 and verbose output for debugging."""
        
        opts = {
            "quiet": False,           # DEBUG: show yt-dlp output
            "no_warnings": False,     # DEBUG: show warnings
            "verbose": True,          # DEBUG: full verbose mode
            "socket_timeout": 15,     # Don't hang forever
            "retries": 3,
            "fragment_retries": 3,
            "file_access_retries": 3,
            "extractor_retries": 3,
            "force_ipv4": True,       # Fix for cloud server hanging [^2^]
            "geo_bypass": True,
            "skip_unavailable_fragments": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        # CRITICAL: Use cookies.txt if it exists
        cookie_path = Path("cookies.txt")
        if cookie_path.exists():
            logger.info(f"Using cookies file: {cookie_path}")
            opts["cookiefile"] = str(cookie_path)
            opts["extractor_args"] = {
                "youtube": {
                    "player_client": ["web"],
                    "player_skip": ["configs"],
                }
            }
        else:
            logger.warning("No cookies.txt found - falling back to tv_embedded")
            # Fallback to tv_embedded (lower quality but may bypass bot check)
            opts["extractor_args"] = {
                "youtube": {
                    "player_client": ["tv_embedded"],
                    "player_skip": ["webpage", "configs", "js"],
                }
            }

        return opts
    
    def _progress_hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 1)
            downloaded = d.get("downloaded_bytes", 0)
            self.progress = int(downloaded / total * 100) if total > 0 else 0
            self.status = "downloading"
            logger.info(f"Progress: {self.progress}%")
        elif d["status"] == "finished":
            self.progress = 99
            self.status = "downloading"

    def _postprocessor_hook(self, d):
        if d["status"] == "finished":
            self.progress = 100
            self.status = "done"
            self.filename = d["info_dict"].get("filepath") or d.get("filepath")
            logger.info(f"Done: {self.filename}")

    def download(self):
        try:
            opts = {**self._base_options(), **self.get_options()}
            opts["progress_hooks"] = [self._progress_hook]
            opts["postprocessor_hooks"] = [self._postprocessor_hook]
            
            logger.info(f"Starting download with options: {opts.get('extractor_args')}")
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                if not self.filename and info:
                    self.filename = ydl.prepare_filename(info)
                    self.progress = 100
                    self.status = "done"
                    
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            self.status = "error"
            self.error = str(e)


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