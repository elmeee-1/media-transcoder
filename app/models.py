from pathlib import Path
import yt_dlp
import os
import threading
from abc import ABC, abstractmethod


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
    def _progress_hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 1)
            downloaded = d.get("downloaded_bytes", 0)
            self.progress = int(downloaded / total * 100)
            self.status = "downloading"
        elif d["status"] == "finished":
            self.progress = 99
            self.status = "downloading"  # still processing via FFmpeg

    def _postprocessor_hook(self, d):
        if d["status"] == "finished":
            self.progress = 100
            self.status = "done"
            self.filename = d["info_dict"].get("filepath") or d.get("filepath")

    def download(self):
        try:
            opts = self.get_options()
            opts["progress_hooks"] = [self._progress_hook]
            opts["postprocessor_hooks"] = [self._postprocessor_hook]
            with yt_dlp.YoutubeDL() as ydl:
                ydl.download([self.url])
        except Exception as e:
            self.status = "error"
            self.error = str(e)

class VideoDownloader(MediaDownloader):
    def get_options(self) -> dict:
        return {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": f"{self.output_dir}/%(title)s.%(ext)s",
            "merge_output_format": "mp4",
            "ffmpeg_location": "C:\\Users\\mahdi\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.1.1-full_build\\bin",
        }

class AudioDownloader(MediaDownloader):
    def get_options(self) -> dict:
        return {
            "format": "bestaudio/best",
            "outtmpl": f"{self.output_dir}/%(title)s.%(ext)s",
            "ffmpeg_location": "C:\\Users\\mahdi\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.1.1-full_build\\bin",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        


class DownloadManager:
    def __init__(self):
        self.jobs: dict[str, MediaDownloader] = {}

    def create_job(self, job_id, url, media_type, save_path):
        if media_type == "audio":
            downloader = AudioDownloader(url, save_path)
        else:
            downloader = VideoDownloader(url, save_path)

        self.jobs[job_id] = downloader

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
            "error": job.error
        }

    def delete_job(self, job_id: str):
        job = self.jobs.get(job_id)

        if job and job.filename and os.path.exists(job.filename):
            os.remove(job.filename)

        self.jobs.pop(job_id, None)


manager = DownloadManager()