#models.py
import yt_dlp
import os
import threading
from abc import ABC, abstractmethod

class MediaDownloader(ABC):
    def __init__(self, url: str, output_dir: str = "downloads"):
        self.url = url
        self.output_dir = output_dir
        self.progress = 0
        self.status = "pending"  # pending → downloading → done / error
        self.filename = None
        os.makedirs(self.output_dir, exist_ok=True)

    @abstractmethod
    def get_options(self) -> dict:
        pass

    def _progress_hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 1)
            downloaded = d.get("downloaded_bytes", 0)
            self.progress = int(downloaded / total * 100)
            self.status = "downloading"

        elif d["status"] == "finished":
            self.progress = 100
            self.status = "done"
            self.filename = d["filename"]

    def download(self):
        try:
            opts = self.get_options()
            opts["progress_hooks"] = [self._progress_hook]
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])
        except Exception as e:
            self.status = "error"
            self.error = str(e)


# ─── Video Downloader (MP4) ────────────────────────────────────────

class VideoDownloader(MediaDownloader):
    def get_options(self) -> dict:
        return {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": f"{self.output_dir}/%(title)s.%(ext)s",
            "merge_output_format": "mp4",
        }


# ─── Audio Downloader (MP3) ────────────────────────────────────────

class AudioDownloader(MediaDownloader):
    def get_options(self) -> dict:
        return {
            "format": "bestaudio/best",
            "outtmpl": f"{self.output_dir}/%(title)s.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }


# ─── Download Manager (Factory Pattern) ───────────────────────────

class DownloadManager:
    def __init__(self):
        self.jobs: dict[str, MediaDownloader] = {}  # job_id → downloader

    def create_job(self, job_id: str, url: str, media_type: str) -> MediaDownloader:
        if media_type == "audio":
            downloader = AudioDownloader(url)
        else:
            downloader = VideoDownloader(url)

        self.jobs[job_id] = downloader
        return downloader

    def start_job(self, job_id: str):
        downloader = self.jobs[job_id]
        thread = threading.Thread(target=downloader.download)
        thread.daemon = True
        thread.start()

    def get_status(self, job_id: str) -> dict:
        job = self.jobs.get(job_id)
        if not job:
            return {"status": "not_found"}
        return {
            "status": job.status,
            "progress": job.progress,
            "filename": job.filename,
        }

    def delete_job(self, job_id: str):
        job = self.jobs.get(job_id)
        if job and job.filename and os.path.exists(job.filename):
            os.remove(job.filename)
        self.jobs.pop(job_id, None)


# ─── Singleton instance (shared across the app) ───────────────────
manager = DownloadManager()