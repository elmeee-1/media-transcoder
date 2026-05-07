from pathlib import Path
import yt_dlp
import os
import threading
from abc import ABC, abstractmethod


# Default HTTP headers to mimic a real browser
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


class MediaDownloader(ABC):
    """Abstract base class for media downloading with browser-like behavior."""
    
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
        """Get yt-dlp options for this downloader type."""
        pass
    
    def _get_base_options(self) -> dict:
        """Get common options for all downloaders to handle bot detection."""
        return {
            "http_headers": DEFAULT_HEADERS,
            "user_agent": DEFAULT_HEADERS['User-Agent'],
            "no_check_certificates": True,
            "quiet": False,
            "no_warnings": False,
            "extractor_args": {
                "youtube": {
                    "skip_unavailable_videos": True,
                    "lang": ["en"],
                }
            },
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
            "skip_unavailable_fragments": True,
        }
    
    def _progress_hook(self, d):
        """Update download progress."""
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 1)
            downloaded = d.get("downloaded_bytes", 0)
            self.progress = int(downloaded / total * 100) if total > 0 else 0
            self.status = "downloading"
        elif d["status"] == "finished":
            self.progress = 99
            self.status = "downloading"

    def _postprocessor_hook(self, d):
        """Handle post-processing completion."""
        if d["status"] == "finished":
            self.progress = 100
            self.status = "done"
            self.filename = d["info_dict"].get("filepath") or d.get("filepath")

    def download(self):
        """Start the download process."""
        try:
            opts = self.get_options()
            opts["progress_hooks"] = [self._progress_hook]
            opts["postprocessor_hooks"] = [self._postprocessor_hook]
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])
        except Exception as e:
            self.status = "error"
            self.error = str(e)


class VideoDownloader(MediaDownloader):
    """Download YouTube videos in specified quality."""
    
    def __init__(self, url: str, quality: str = "720p", output_dir: str = "downloads"):
        super().__init__(url, output_dir)
        self.quality = quality

    def get_options(self) -> dict:
        """Get options for video download."""
        quality_map = {
            "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        }
        opts = self._get_base_options()
        opts.update({
            "format": quality_map.get(self.quality, "bestvideo+bestaudio/best"),
            "outtmpl": os.path.join(self.output_dir, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
        })
        return opts


class AudioDownloader(MediaDownloader):
    """Extract audio from YouTube videos as MP3."""
    
    def __init__(self, url: str, quality: str = "192kbps", output_dir: str = "downloads"):
        super().__init__(url, output_dir)
        self.quality = quality

    def get_options(self) -> dict:
        """Get options for audio extraction."""
        quality_map = {
            "128kbps": "128",
            "192kbps": "192",
            "256kbps": "256",
        }
        opts = self._get_base_options()
        opts.update({
            "format": "bestaudio/best",
            "outtmpl": os.path.join(self.output_dir, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality_map.get(self.quality, "192"),
            }],
        })
        return opts

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

    def delete_job(self,job_id: str):
        job = self.jobs.get(job_id)

        if job and job.filename and os.path.exists(job.filename):
            try:
                os.remove(job.filename)
            except OSError:
                pass
        self.jobs.pop(job_id,None)


manager = DownloadManager()