"""
FastAPI backend for Media Transcoder application.
Handles YouTube video/audio downloads with real-time progress tracking.
"""

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import yt_dlp
from app.models import manager

app = FastAPI(title="Media Transcoder", version="1.0.0")

# Add CORS middleware for better cross-origin support
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home(request: Request):
    """Serve the home page."""
    return templates.TemplateResponse(request, "index.html")


@app.post("/download")
async def start_download(request: Request):
    """
    Start a new download job.
    
    Expected JSON body:
    {
        "url": "https://...",
        "media_type": "video" or "audio",
        "quality": "720p" or "192kbps", etc.
    }
    """
    try:
        data = await request.json()
        url = data.get("url", "").strip()
        media_type = data.get("media_type", "video").lower()
        quality = data.get("quality", "720p")

        if not url:
            return JSONResponse(
                {"error": "No URL provided"},
                status_code=400
            )

        if media_type not in ["video", "audio"]:
            return JSONResponse(
                {"error": "Invalid media_type. Use 'video' or 'audio'."},
                status_code=400
            )

        job_id = str(uuid.uuid4())
        manager.create_job(job_id, url, media_type, quality)
        manager.start_job(job_id)

        return JSONResponse({"job_id": job_id})
    
    except Exception as e:
        return JSONResponse(
            {"error": f"Server error: {str(e)}"},
            status_code=500
        )


@app.get("/status/{job_id}")
def get_status(job_id: str):
    """Get the status of a download job."""
    return JSONResponse(manager.get_status(job_id))


@app.get("/file/{job_id}")
def download_file(job_id: str):
    """Download the completed file."""
    status = manager.get_status(job_id)

    if status["status"] != "done":
        return JSONResponse(
            {"error": "File not ready"},
            status_code=400
        )

    filepath = status["filename"]

    if not filepath or not os.path.exists(filepath):
        return JSONResponse(
            {"error": "File not found"},
            status_code=404
        )

    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type="application/octet-stream"
    )


@app.delete("/job/{job_id}")
def delete_job(job_id: str):
    """Delete a job and clean up its files."""
    manager.delete_job(job_id)
    return JSONResponse({"message": "Job deleted"})


@app.get("/debug")
def debug_info():
    """Return debug information for deployed service health checks."""
    return JSONResponse({
        "yt_dlp_version": yt_dlp.__version__,
        "job_count": len(manager.jobs),
        "downloads_dir": os.path.abspath("downloads"),
    })