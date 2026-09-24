from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DOWNLOAD_DIR = BASE_DIR / "downloads"
JOB_TTL_SECONDS = 60 * 60
CLEANUP_INTERVAL_SECONDS = 300
MAX_WORKERS = 2


def ensure_directories() -> None:
    DOWNLOAD_DIR.mkdir(exist_ok=True)
