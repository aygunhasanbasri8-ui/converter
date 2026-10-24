from __future__ import annotations

import asyncio
import json
import shutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

from .config import (
    CLEANUP_INTERVAL_SECONDS,
    DOWNLOAD_DIR,
    JOB_TTL_SECONDS,
    MAX_WORKERS,
    STATIC_DIR,
    ensure_directories,
)
from .downloader import DownloadService, available_qualities
from .errors import readable_error
from .jobs import JobStore
from .models import DownloadRequest, InfoRequest

ensure_directories()
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="download")
jobs = JobStore(DOWNLOAD_DIR, executor, JOB_TTL_SECONDS)
downloader = DownloadService(DOWNLOAD_DIR, jobs)


def cleanup_worker(stop_event: threading.Event) -> None:
    while not stop_event.wait(CLEANUP_INTERVAL_SECONDS):
        jobs.remove_expired()


@asynccontextmanager
async def lifespan(_: FastAPI):
    stop_event = threading.Event()
    cleanup_thread = threading.Thread(target=cleanup_worker, args=(stop_event,), name="cleanup", daemon=True)
    cleanup_thread.start()
    if shutil.which("ffmpeg") is None:
        print("ffmpeg bulunamadı. MP3 dönüşümü ve MP4 birleştirmesi çalışmaz.")
    try:
        yield
    finally:
        stop_event.set()
        cleanup_thread.join(timeout=1)
        executor.shutdown(wait=False, cancel_futures=True)


app = FastAPI(title="Video İndirici", docs_url=None, redoc_url=None, lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    content = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content)


@app.post("/api/info")
def info(request: InfoRequest) -> dict[str, Any]:
    try:
        data = downloader.inspect(str(request.url))
    except Exception as error:
        raise HTTPException(status_code=400, detail=readable_error(error)) from error

    return {
        "title": data.get("title"),
        "uploader": data.get("uploader") or data.get("channel"),
        "duration": data.get("duration"),
        "thumbnail": data.get("thumbnail"),
        "qualities": available_qualities(data),
    }


@app.post("/api/download")
def start_download(request: DownloadRequest) -> dict[str, str]:
    job_id = uuid.uuid4().hex
    jobs.create(job_id, request.format)
    jobs.submit(lambda: downloader.download(job_id, str(request.url), request.format, request.quality))
    return {"job_id": job_id}


def _public(job: dict[str, Any]) -> dict[str, Any]:
    # Sunucudaki tam yol istemciyi ilgilendirmiyor.
    job.pop("path", None)
    return job


@app.get("/api/progress/{job_id}")
def progress(job_id: str) -> dict[str, Any]:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="İş bulunamadı.")
    return _public(job)


EVENT_CHECK_SECONDS = 0.25
EVENT_KEEPALIVE_SECONDS = 15.0
FINISHED_STATES = ("ready", "error")


@app.get("/api/events/{job_id}")
async def events(job_id: str, request: Request) -> StreamingResponse:
    """İlerlemeyi Server-Sent Events ile iter; istemci her 600 ms'de sormak zorunda kalmaz.

    Yalnızca iş değiştiğinde olay gönderiliyor. İş bitince akış kapanıyor.
    """
    if jobs.get(job_id) is None:
        raise HTTPException(status_code=404, detail="İş bulunamadı.")

    async def stream():
        last_update = None
        last_sent = time.monotonic()
        while not await request.is_disconnected():
            job = jobs.get(job_id)
            if job is None:
                # Süresi dolup silindi; istemci yoklamaya düşmesin diye hata olarak bildir
                yield "data: " + json.dumps({"state": "error", "error": "İş bulunamadı."}) + "\n\n"
                return
            if job["updated_at"] != last_update:
                last_update = job["updated_at"]
                last_sent = time.monotonic()
                yield "data: " + json.dumps(_public(job), ensure_ascii=False) + "\n\n"
                if job["state"] in FINISHED_STATES:
                    return
            elif time.monotonic() - last_sent > EVENT_KEEPALIVE_SECONDS:
                # Proxy'ler boşta kalan bağlantıyı kesmesin
                last_sent = time.monotonic()
                yield ": ping\n\n"
            await asyncio.sleep(EVENT_CHECK_SECONDS)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/file/{job_id}")
def file(job_id: str) -> FileResponse:
    job = jobs.get(job_id)
    if job is None or job.get("state") != "ready":
        raise HTTPException(status_code=404, detail="Dosya hazır değil.")

    path = DOWNLOAD_DIR / job_id / job["filename"]
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Dosya silinmiş.")

    return FileResponse(path, filename=path.name, media_type="application/octet-stream")
