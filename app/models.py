from pathlib import Path
import yt_dlp
import os
import threading
import time
from abc import ABC, abstractmethod


class MediaDownloader(ABC):
    """Base class for media downloading with robust YouTube support."""
    
    def __init__(self, url: str, output_dir: str):
        self.url = url
        self.output_dir = str(output_dir)
        self.progress = 0
        self.status = "pending"
        self.filename = None
        self.error = None
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "cache"), exist_ok=True)

    @abstractmethod
    def get_options(self) -> dict:
        """Get downloader-specific options."""
        pass
    
    def _get_base_options(self, retry_attempt: int = 0) -> dict:
        """Get base yt-dlp options with smart retry logic."""
        
        # Rotate user agents based on retry attempt
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        ]
        
        user_agent = user_agents[retry_attempt % len(user_agents)]
        
        opts = {
            "quiet": False,
            "verbose": True,
            "no_warnings": False,
            "noprogress": False,
            "socket_timeout": 30,
            "retries": 25,
            "fragment_retries": 25,
            "file_access_retries": 20,
            "extractor_retries": 25,
            "http_headers": {
                "User-Agent": user_agent,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
            },
            "geo_bypass": True,
            "geo_bypass_country": "US",
            "skip_unavailable_fragments": True,
            "allow_unplayable_formats": True,
            "check_formats": True,
            "outtmpl_na_placeholder": "",
            "cachedir": os.path.join(self.output_dir, "cache"),
            "rm_cache_dir": False,
        }

        # Rotate player clients on retry
        player_clients = [
            ["android", "tv_embedded", "ios"],
            ["ios", "tv_embedded", "android", "web"],
            ["mweb", "web_embedded", "tv_embedded"],
            ["web", "web_embedded", "mweb", "android"],
        ]
        
        client_set = player_clients[retry_attempt % len(player_clients)]

        opts["extractor_args"] = {
            "youtube": {
                "player_client": ["web", "ios"],  # Simpler client list
                "skip_webpage": False,
            }
        }

        # Use cookies if available
        cookie_path = Path("cookies.txt")
        if cookie_path.exists():
            opts["cookiefile"] = str(cookie_path)

        return opts
    
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
        """Download with automatic retry logic and fallback strategies."""
        max_retries = 3
        
        # Set environment for yt-dlp
        os.environ["YTDLP_NO_WARNINGS"] = "1"
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff: 5s, 10s, 15s
                    wait_time = 5 * attempt
                    self.status = "pending"
                    self.error = f"Retrying... (attempt {attempt + 1}/{max_retries})"
                    time.sleep(wait_time)
                
                opts = {**self._get_base_options(attempt), **self.get_options()}
                opts["progress_hooks"] = [self._progress_hook]
                opts["postprocessor_hooks"] = [self._postprocessor_hook]
                
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(self.url, download=True)
                    if not self.filename and info:
                        self.filename = ydl.prepare_filename(info)
                        self.progress = 100
                        self.status = "done"
                    return  # Success - exit retry loop
                    
            except Exception as e:
                error_msg = str(e).lower()
                self.status = "error"
                self.error = self._parse_error_message(error_msg, str(e))
                
                # Only retry on specific recoverable errors
                if attempt < max_retries - 1:
                    if any(keyword in error_msg for keyword in [
                        "innertube_context",  # NEW: Retry on context errors
                        "player response", 
                        "unable to extract",
                        "403",
                        "429",  # Too many requests
                        "timeout",
                        "connection reset",
                        "failed to extract",
                    ]):
                        continue  # Retry with next attempt
                
                # Final error - don't retry
                break
    
    def _parse_error_message(self, error_msg: str, full_error: str) -> str:
        """Parse YouTube errors and provide helpful messages."""
        
        if "innertube_context" in error_msg or "innertube context" in error_msg:
            return "🔄 YouTube API context error. Retrying with different configuration..."
        
        if "sign in" in error_msg or "bot" in error_msg:
            return "🤖 YouTube detected automation. Wait 10 minutes and try again."
        
        if "failed to extract any player response" in error_msg or "unable to extract video data" in error_msg:
            return "❌ Cannot extract video data. Try:\n• A different video\n• In 10 minutes\n• Your own uploaded video"
        
        if "video not available" in error_msg or "not available" in error_msg:
            return "⛔ Video unavailable (deleted, private, or region-blocked)"
        
        if "age restricted" in error_msg or "age restriction" in error_msg:
            return "🔞 Age-restricted (need YouTube login)"
        
        if "403" in error_msg or "forbidden" in error_msg:
            return "⚠️ Access forbidden by YouTube. Try again later."
        
        if "429" in error_msg or "too many requests" in error_msg:
            return "⏳ YouTube rate limit hit. Wait 30 seconds."
        
        if "connection" in error_msg or "timeout" in error_msg or "reset" in error_msg:
            return "🌐 Network error. Check internet connection."
        
        # Generic error
        return f"❌ Error: {full_error[:120]}"


class VideoDownloader(MediaDownloader):
    """Download YouTube videos."""
    
    def __init__(self, url: str, quality: str = "720p", output_dir: str = "downloads"):
        super().__init__(url, output_dir)
        self.quality = quality

    def get_options(self) -> dict:
        """Get video-specific options."""
        quality_map = {
            "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        }
        return {
            "format": quality_map.get(self.quality, "best"),
            "format_sort": ["res", "ext:mp4:m4a"],
            "outtmpl": os.path.join(self.output_dir, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "postprocessors": [],
            "quiet": False,
        }


class AudioDownloader(MediaDownloader):
    """Extract audio from YouTube videos as MP3."""
    
    def __init__(self, url: str, quality: str = "192kbps", output_dir: str = "downloads"):
        super().__init__(url, output_dir)
        self.quality = quality

    def get_options(self) -> dict:
        """Get audio-specific options."""
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
    """Manage download jobs."""
    
    def __init__(self):
        self.jobs: dict[str, MediaDownloader] = {}

    def create_job(self, job_id: str, url: str, media_type: str, quality: str = "720p") -> MediaDownloader:
        """Create a new download job."""
        if media_type == "audio":
            downloader = AudioDownloader(url, quality)
        else:
            downloader = VideoDownloader(url, quality)
        self.jobs[job_id] = downloader
        return downloader

    def start_job(self, job_id: str):
        """Start a download job in background thread."""
        downloader = self.jobs.get(job_id)
        if not downloader:
            return
        thread = threading.Thread(target=downloader.download, daemon=True)
        thread.start()

    def get_status(self, job_id: str) -> dict:
        """Get status of a job."""
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
        """Delete a job and clean up files."""
        job = self.jobs.get(job_id)
        if job and job.filename and os.path.exists(job.filename):
            try:
                os.remove(job.filename)
            except OSError:
                pass
        self.jobs.pop(job_id, None)


# Global manager instance
manager = DownloadManager()