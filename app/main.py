from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid
import os

from app.models import manager

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ─── Home Page ────────────────────────────────────────────────────

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")
# ─── Start a Download ─────────────────────────────────────────────
@app.post("/download")
async def start_download(request: Request):
    data = await request.json()
    url = data.get("url")
    media_type = data.get("media_type", "video")  # "video" or "audio"

    if not url:
        return JSONResponse({"error": "No URL provided"}, status_code=400)

    job_id = str(uuid.uuid4())
    manager.create_job(job_id, url, media_type)
    manager.start_job(job_id)

    return JSONResponse({"job_id": job_id})


# ─── Check Progress ───────────────────────────────────────────────
@app.get("/status/{job_id}")
def get_status(job_id: str):
    status = manager.get_status(job_id)
    return JSONResponse(status)


# ─── Download the File ────────────────────────────────────────────
@app.get("/file/{job_id}")
def download_file(job_id: str):
    status = manager.get_status(job_id)

    if status["status"] != "done":
        return JSONResponse({"error": "File not ready"}, status_code=400)

    filepath = status["filename"]

    if not filepath or not os.path.exists(filepath):
        return JSONResponse({"error": "File not found"}, status_code=404)

    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type="application/octet-stream"
    )


# ─── Delete a Job ─────────────────────────────────────────────────
@app.delete("/job/{job_id}")
def delete_job(job_id: str):
    manager.delete_job(job_id)
    return JSONResponse({"message": "Job deleted"})