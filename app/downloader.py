from __future__ import annotations

import copy
import shutil
from pathlib import Path
from typing import Any

from .errors import QuietLogger, readable_error
from .jobs import JobStore

BASE_OPTIONS: dict[str, Any] = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
}

FORMAT_OPTIONS: dict[str, dict[str, Any]] = {
    "mp3": {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            },
            {"key": "FFmpegMetadata"},
        ],
    },
    "mp4": {
        "format": "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b[ext=mp4]/b",
        "merge_output_format": "mp4",
        "postprocessors": [{"key": "FFmpegMetadata"}],
    },
}

# İndirme yarıda kalırsa geride bunlar kalıyor, çıktı sanılmasın.
PARTIAL_SUFFIXES = {".part", ".ytdl", ".tmp"}


class DownloadService:
    def __init__(self, download_dir: Path, jobs: JobStore) -> None:
        self._download_dir = download_dir
        self._jobs = jobs

    def inspect(self, url: str) -> dict[str, Any]:
        return _first_entry(_extract(url, {}, download=False))

    def download(self, job_id: str, url: str, output_format: str) -> None:
        target_dir = self._download_dir / job_id
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            data = _extract(url, self._options(target_dir, output_format, job_id), download=True)

            output = _find_output(target_dir, output_format)
            if output is None:
                raise RuntimeError("Çıktı dosyası oluşmadı.")

            self._jobs.update(
                job_id,
                state="ready",
                percent=100.0,
                path=str(output),
                filename=output.name,
                size=output.stat().st_size,
                title=_first_entry(data).get("title") or output.stem,
            )
        except Exception as error:
            shutil.rmtree(target_dir, ignore_errors=True)
            self._jobs.update(job_id, state="error", error=readable_error(error))

    def _options(self, target_dir: Path, output_format: str, job_id: str) -> dict[str, Any]:
        def progress_hook(data: dict[str, Any]) -> None:
            status = data.get("status")
            if status == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                downloaded = data.get("downloaded_bytes") or 0
                self._jobs.update(
                    job_id,
                    state="downloading",
                    percent=round(downloaded / total * 100, 1) if total else None,
                    downloaded=downloaded,
                    total=total,
                    speed=data.get("speed"),
                    eta=data.get("eta"),
                )
            elif status == "finished":
                self._jobs.update(job_id, state="processing", percent=100.0, speed=None, eta=None)

        # Sabit tablo işler arasında paylaşılıyor, yt-dlp'ye kopyası gitsin.
        format_options = copy.deepcopy(FORMAT_OPTIONS["mp3" if output_format == "mp3" else "mp4"])
        return {
            "outtmpl": str(target_dir / "%(title).150B.%(ext)s"),
            "windowsfilenames": True,
            "noprogress": True,
            "progress_hooks": [progress_hook],
            "retries": 3,
            "fragment_retries": 3,
            "concurrent_fragment_downloads": 4,
            "overwrites": True,
            **format_options,
        }


def _extract(url: str, options: dict[str, Any], download: bool) -> Any:
    # yt-dlp ağır bir import; testler ve uygulamanın açılışı ona bağlı kalmasın.
    from yt_dlp import YoutubeDL

    with YoutubeDL({**BASE_OPTIONS, "logger": QuietLogger(), **options}) as ydl:
        return ydl.extract_info(url, download=download)


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
        if path.is_file() and path.suffix.lower() not in PARTIAL_SUFFIXES
    ]
    if not candidates:
        return None
    exact = [path for path in candidates if path.suffix.lower() == f".{output_format}"]
    return max(exact or candidates, key=lambda path: path.stat().st_size)
