from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid
import os
from app.models import manager
from pathlib import Path

app = FastAPI()

app.mount("/templates", StaticFiles(directory="templates"), name="templates")
templates = Jinja2Templates(directory="static")

# ─── Configurable download directory ───
DOWNLOAD_BASE = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
DOWNLOAD_BASE.mkdir(parents=True, exist_ok=True)

# ─── Home Page ────

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")
# ─── Start a Download ──────────────
@app.post("/download")
async def start_download(request: Request):
    data = await request.json()
    url = data.get("url")
    media_type = data.get("media_type", "video")
    user_dir = data.get("save_dir")   

    if not url:
        return JSONResponse({"error": "No URL provided"}, status_code=400)

    # Security: restrict to a safe root
    SAFE_ROOT = Path("/allowed/downloads").resolve()
    if user_dir:
        target = (SAFE_ROOT / user_dir).resolve()
        if not str(target).startswith(str(SAFE_ROOT)):
            return JSONResponse({"error": "Invalid save directory"}, status_code=400)
        target.mkdir(parents=True, exist_ok=True)
    else:
        target = Path("./downloads")  

    job_id = str(uuid.uuid4())
    job_dir = target / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    manager.create_job(job_id, url, media_type, save_path=job_dir)
    manager.start_job(job_id)

    return JSONResponse({"job_id": job_id})

# ─── Check Progress ────────
@app.get("/status/{job_id}")
def get_status(job_id: str):
    status = manager.get_status(job_id)
    return JSONResponse(status)


# ─── Download the File ───────────────
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


# ─── Delete a Job ────────────────────
@app.delete("/job/{job_id}")
def delete_job(job_id: str):
    manager.delete_job(job_id)
    return JSONResponse({"message": "Job deleted"})