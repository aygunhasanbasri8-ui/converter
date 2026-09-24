from __future__ import annotations

import shutil
import threading
import time
from concurrent.futures import Executor
from pathlib import Path
from typing import Any, Callable


class JobStore:
    def __init__(self, download_dir: Path, executor: Executor, ttl_seconds: int) -> None:
        self._download_dir = download_dir
        self._executor = executor
        self._ttl_seconds = ttl_seconds
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self, job_id: str, output_format: str) -> None:
        now = time.time()
        with self._lock:
            self._jobs[job_id] = {
                "state": "queued",
                "percent": None,
                "format": output_format,
                "created_at": now,
                "updated_at": now,
            }

    def update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.update(fields, updated_at=time.time())

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def submit(self, job_id: str, task: Callable[[], None]) -> None:
        self._executor.submit(task)

    def remove_expired(self) -> None:
        now = time.time()
        expired_ids: list[str] = []
        with self._lock:
            for job_id, job in list(self._jobs.items()):
                if now - job.get("updated_at", now) > self._ttl_seconds:
                    expired_ids.append(job_id)
                    del self._jobs[job_id]
        for job_id in expired_ids:
            shutil.rmtree(self._download_dir / job_id, ignore_errors=True)
