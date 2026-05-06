from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uuid
import os
from fastapi.staticfiles import StaticFiles
from app.models import manager
from pathlib import Path

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

DOWNLOAD_BASE = Path("./downloads")
DOWNLOAD_BASE.mkdir(parents=True, exist_ok=True)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


@app.post("/download")
async def start_download(request: Request):
    data = await request.json()

    url = data.get("url")
    media_type = data.get("media_type", "video")

    if not url:
        return JSONResponse({"error": "No URL provided"}, status_code=400)

    job_id = str(uuid.uuid4())
    job_dir = DOWNLOAD_BASE / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    manager.create_job(job_id, url, media_type, job_dir)
    manager.start_job(job_id)

    return JSONResponse({"job_id": job_id})


@app.get("/status/{job_id}")
def get_status(job_id: str):
    return JSONResponse(manager.get_status(job_id))


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


@app.delete("/job/{job_id}")
def delete_job(job_id: str):
    manager.delete_job(job_id)
    return JSONResponse({"message": "Job deleted"})


app.mount("/static", StaticFiles(directory="static"), name="static")