from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable

from .errors import QuietLogger, readable_error
from .jobs import JobStore


class DownloadService:
    def __init__(self, download_dir: Path, jobs: JobStore) -> None:
        self._download_dir = download_dir
        self._jobs = jobs

    def inspect(self, url: str) -> dict[str, Any]:
        from yt_dlp import YoutubeDL

        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "logger": QuietLogger(),
        }
        with YoutubeDL(options) as ydl:
            data = ydl.extract_info(url, download=False)
        return _first_entry(data)

    def download(self, job_id: str, url: str, output_format: str) -> None:
        from yt_dlp import YoutubeDL

        target_dir = self._download_dir / job_id
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            with YoutubeDL(self._options(target_dir, output_format, job_id)) as ydl:
                data = ydl.extract_info(url, download=True)

            output = _find_output(target_dir, output_format)
            if output is None:
                raise RuntimeError("Çıktı dosyası oluşmadı.")

            info = _first_entry(data)
            self._jobs.update(
                job_id,
                state="ready",
                percent=100.0,
                path=str(output),
                filename=output.name,
                size=output.stat().st_size,
                title=info.get("title") or output.stem,
            )
        except Exception as error:
            shutil.rmtree(target_dir, ignore_errors=True)
            self._jobs.update(job_id, state="error", error=readable_error(error))

    def _options(
        self, target_dir: Path, output_format: str, job_id: str
    ) -> dict[str, Any]:
        def progress_hook(data: dict[str, Any]) -> None:
            if data.get("status") == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                downloaded = data.get("downloaded_bytes") or 0
                percent = round(downloaded / total * 100, 1) if total else None
                self._jobs.update(
                    job_id,
                    state="downloading",
                    percent=percent,
                    downloaded=downloaded,
                    total=total,
                    speed=data.get("speed"),
                    eta=data.get("eta"),
                )
            elif data.get("status") == "finished":
                self._jobs.update(
                    job_id, state="processing", percent=100.0, speed=None, eta=None
                )

        options: dict[str, Any] = {
            "logger": QuietLogger(),
            "outtmpl": str(target_dir / "%(title).150B.%(ext)s"),
            "noplaylist": True,
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "progress_hooks": [progress_hook],
            "retries": 3,
            "fragment_retries": 3,
            "concurrent_fragment_downloads": 4,
            "overwrites": True,
        }
        if output_format == "mp3":
            options.update(
                format="bestaudio/best",
                postprocessors=[
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    },
                    {"key": "FFmpegMetadata"},
                ],
            )
        else:
            options.update(
                format="bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b[ext=mp4]/b",
                merge_output_format="mp4",
                postprocessors=[{"key": "FFmpegMetadata"}],
            )
        return options


def _first_entry(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    entries = data.get("entries")
    if isinstance(entries, list) and entries:
        first = entries[0]
        return first if isinstance(first, dict) else {}
    return data


def _find_output(target_dir: Path, output_format: str) -> Path | None:
    candidates = [
        path
        for path in target_dir.iterdir()
        if path.is_file() and path.suffix.lower() not in {".part", ".ytdl", ".tmp"}
    ]
    if not candidates:
        return None
    exact = [path for path in candidates if path.suffix.lower() == f".{output_format}"]
    return max(exact or candidates, key=lambda path: path.stat().st_size)
