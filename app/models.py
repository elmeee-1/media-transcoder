from pathlib import Path
import yt_dlp
import os
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MediaDownloader:
    
    def __init__(self, url: str, output_dir: str):
        self.url = url
        self.output_dir = str(output_dir)
        self.progress = 0
        self.status = "pending"
        self.filename = None
        self.error = None
        os.makedirs(self.output_dir, exist_ok=True)

    def _base_options(self, use_tv: bool = True) -> dict:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 15,
            "retries": 5,
            "fragment_retries": 5,
            "force_ipv4": True,
            "geo_bypass": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
                }
        
        proxy = os.getenv("PROXY_URL", "")
        if proxy:
            opts["proxy"] = proxy
            logger.info(f"Using proxy")
        
        if use_tv:
            # tv_embedded bypasses bot check, limited to 720p max
            opts["extractor_args"] = {
                "youtube": {
                    "player_client": ["tv_embedded"],
                    "player_skip": ["webpage", "configs", "js"],
                }
            }
            logger.info("Using tv_embedded client")
        else:
            # Fallback: web client + cookies (if available)
            cookie_path = Path("cookies.txt")
            if cookie_path.exists():
                opts["cookiefile"] = str(cookie_path)
                opts["extractor_args"] = {
                    "youtube": {
                        "player_client": ["web"],
                        "player_skip": ["configs"],
                    }
                }
                logger.info("Using web client with cookies")
            else:
                opts["extractor_args"] = {
                    "youtube": {
                        "player_client": ["android"],
                    }
                }
                logger.info("Using android client (no cookies)")

        return opts
    
    def _progress_hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 1)
            downloaded = d.get("downloaded_bytes", 0)
            self.progress = int(downloaded / total * 100) if total > 0 else 0
            self.status = "downloading"
        elif d["status"] == "finished":
            self.progress = 99

    def _postprocessor_hook(self, d):
        if d["status"] == "finished":
            self.progress = 100
            self.status = "done"
            self.filename = d["info_dict"].get("filepath") or d.get("filepath")

    def download(self):
        # Try tv_embedded first
        for attempt, use_tv in enumerate([True, False]):
            try:
                if attempt > 0:
                    self.status = "pending"
                    time.sleep(3)
                
                opts = {**self._base_options(use_tv), **self.get_options()}
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
                logger.error(f"Attempt {attempt + 1} failed: {error_msg[:100]}")
                
                if "bot" in error_msg or "sign in" in error_msg:
                    continue  # Try next strategy
                
                self.status = "error"
                self.error = str(e)[:200]
                return
        
        self.status = "error"
        self.error = "YouTube blocked all attempts. Try a proxy or different video."

    def get_options(self) -> dict:
        raise NotImplementedError


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
        self.jobs = {}

    def create_job(self, job_id: str, url: str, media_type: str, quality: str = "720p"):
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