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

    def _base_options(self) -> dict:

        BASE_DIR = Path(__file__).resolve().parent.parent
        COOKIE_FILE = BASE_DIR / "www.youtube.com_cookies.txt"

        opts = {
            "quiet": True,
            "no_warnings": True,

            "socket_timeout": 30,

            "retries": 10,
            "fragment_retries": 10,
            "file_access_retries": 5,
            "extractor_retries": 10,

            "force_ipv4": True,
            "geo_bypass": True,

            "skip_unavailable_fragments": True,

            "cookiefile": str(COOKIE_FILE),

            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },

            "extractor_args": {
                "youtube": {
                    "player_client": [
                        "android",
                        "web",
                        "tv_embedded"
                    ],
                    "player_skip": [
                        "webpage",
                        "configs",
                        "js"
                    ],
                }
            },
        }

        # REMOVE THIS PROXY IF YOUTUBE STILL BLOCKS YOU
        proxy = "http://rujjnilm:ngm1m0ee1i52@31.59.20.176:6754"

        if proxy:
            opts["proxy"] = proxy
            logger.info("Proxy enabled")

        return opts

    def _progress_hook(self, d):

        if d["status"] == "downloading":

            total = (
                d.get("total_bytes")
                or d.get("total_bytes_estimate")
                or 1
            )

            downloaded = d.get("downloaded_bytes", 0)

            self.progress = int(downloaded / total * 100)

            self.status = "downloading"

        elif d["status"] == "finished":

            self.progress = 99

    def _postprocessor_hook(self, d):

        if d["status"] == "finished":

            self.progress = 100
            self.status = "done"

            self.filename = (
                d["info_dict"].get("filepath")
                or d.get("filepath")
            )

    def download(self):

        strategies = [
            "android",
            "web",
            "tv_embedded",
        ]

        for client in strategies:

            try:

                self.status = "pending"

                time.sleep(1)

                opts = {
                    **self._base_options(),
                    **self.get_options(),
                }

                opts["progress_hooks"] = [self._progress_hook]
                opts["postprocessor_hooks"] = [self._postprocessor_hook]

                opts["extractor_args"]["youtube"]["player_client"] = [
                    client
                ]

                logger.info(f"Trying {client}...")

                with yt_dlp.YoutubeDL(opts) as ydl:

                    info = ydl.extract_info(
                        self.url,
                        download=True
                    )

                    if not self.filename and info:

                        self.filename = ydl.prepare_filename(info)

                        self.progress = 100
                        self.status = "done"

                    logger.info(f"Success with {client}!")

                    return

            except Exception as e:

                error_msg = str(e).lower()

                logger.error(
                    f"{client} failed: {error_msg[:200]}"
                )

                if (
                    "timeout" in error_msg
                    or "timed out" in error_msg
                ):
                    continue

                if (
                    "confirm you’re not a bot" in error_msg
                    or "confirm you're not a bot" in error_msg
                    or "sign in" in error_msg
                ):
                    continue

                continue

        self.status = "error"
        self.error = (
            "All download methods failed. "
            "YouTube blocked the request or proxy."
        )

    def get_options(self) -> dict:
        raise NotImplementedError


class VideoDownloader(MediaDownloader):

    def __init__(
        self,
        url: str,
        quality: str = "720p",
        output_dir: str = "downloads"
    ):

        super().__init__(url, output_dir)

        self.quality = quality

    def get_options(self) -> dict:

        quality_map = {
            "360p": "bestvideo[height<=360]+bestaudio/best",
            "480p": "bestvideo[height<=480]+bestaudio/best",
            "720p": "bestvideo[height<=720]+bestaudio/best",
        }

        return {
            "format": quality_map.get(
                self.quality,
                "bestvideo+bestaudio/best"
            ),

            "outtmpl": os.path.join(
                self.output_dir,
                "%(title)s.%(ext)s"
            ),

            "merge_output_format": "mp4",
        }


class AudioDownloader(MediaDownloader):

    def __init__(
        self,
        url: str,
        quality: str = "192kbps",
        output_dir: str = "downloads"
    ):

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

            "outtmpl": os.path.join(
                self.output_dir,
                "%(title)s.%(ext)s"
            ),

            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality_map.get(
                    self.quality,
                    "192"
                ),
            }],
        }


class DownloadManager:

    def __init__(self):
        self.jobs = {}

    def create_job(
        self,
        job_id: str,
        url: str,
        media_type: str,
        quality: str = "720p"
    ):

        if media_type == "audio":

            downloader = AudioDownloader(
                url,
                quality
            )

        else:

            downloader = VideoDownloader(
                url,
                quality
            )

        self.jobs[job_id] = downloader

        return downloader

    def start_job(self, job_id: str):

        downloader = self.jobs.get(job_id)

        if not downloader:
            return

        thread = threading.Thread(
            target=downloader.download,
            daemon=True
        )

        thread.start()

    def get_status(self, job_id: str) -> dict:

        job = self.jobs.get(job_id)

        if not job:

            return {
                "status": "not_found",
                "progress": 0
            }

        return {
            "status": job.status,
            "progress": job.progress,
            "filename": job.filename,
            "error": job.error
        }

    def delete_job(self, job_id: str):

        job = self.jobs.get(job_id)

        if (
            job
            and job.filename
            and os.path.exists(job.filename)
        ):

            try:
                os.remove(job.filename)

            except OSError:
                pass

        self.jobs.pop(job_id, None)


manager = DownloadManager()