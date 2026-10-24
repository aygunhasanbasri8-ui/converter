# Video Downloader

English | [Türkçe](README.tr.md)

A small app that downloads the video you give a link to as **MP4** (video + audio) or
**MP3** (192 kbps audio), running entirely on your own machine. yt-dlp does the downloading
and ffmpeg does the conversion.

## Features

- Download from a link as MP4 (best video + audio) or MP3 (192 kbps).
- Shows the title, uploader, duration and thumbnail as soon as a link is pasted.
- Download progress, speed and remaining time; the MP3 conversion and MP4 merge steps are shown separately.
- Jobs run in the background in a worker pool; extra ones wait in a queue.
- Finished files are deleted automatically after one hour.
- Clear error messages (private video, unsupported link, missing ffmpeg, etc.). The messages are in Turkish.
- Listens on `127.0.0.1` only.

Stack: FastAPI, Uvicorn, yt-dlp, pydantic, ffmpeg.

## Installation

ffmpeg is required; MP3 conversion and merging audio with video for MP4 are done with it.

| System | Command |
|---|---|
| Windows | `winget install Gyan.FFmpeg` |
| macOS | `brew install ffmpeg` |
| Ubuntu | `sudo apt install ffmpeg` |

Then install the Python packages and start the app:

```bash
pip install -r requirements.txt
python main.py
```

Open `http://127.0.0.1:8000` in the browser.

For the tests:

```bash
python -m unittest discover -s tests
```

## HTTP endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | The UI |
| POST | `/api/info` | Body: `{"url": ...}`. Returns title, uploader, duration and thumbnail |
| POST | `/api/download` | Body: `{"url": ..., "format": "mp4" \| "mp3"}`. Returns `{"job_id": ...}` |
| GET | `/api/progress/{job_id}` | Job state (`queued`, `downloading`, `processing`, `ready`, `error`) and progress |
| GET | `/api/file/{job_id}` | Downloads the finished file |

## Structure

- `main.py`: starts Uvicorn.
- `app/main.py`: the FastAPI app and the HTTP endpoints.
- `app/downloader.py`: yt-dlp options, downloading and locating the output file.
- `app/jobs.py`: job records, the worker pool and cleanup of old files.
- `app/models.py`: request models and URL validation.
- `app/errors.py`: turns yt-dlp errors into messages the user can understand.
- `app/config.py`: directories, durations and the worker count.
- `static/index.html`: the UI.

Every download lands in `downloads/<job_id>/` and is deleted after an hour. At most
`MAX_WORKERS` downloads run at the same time; the rest wait in a queue.

## Flow

1. When a link is pasted, `POST /api/info` fetches the title, duration and thumbnail.
2. `POST /api/download` opens a job record and hands the download to the worker pool.
3. The UI polls `GET /api/progress/{job_id}` every 600 ms.
4. When the job finishes, the file is saved through `GET /api/file/{job_id}`.

When MP4 is selected but the source has no MP4, yt-dlp downloads the best available format;
the file extension may therefore differ.

## Settings

| Setting | File |
|---|---|
| MP3 bit rate (192 kbps), MP4 quality selection | `app/downloader.py` |
| File retention (1 hour), cleanup interval (5 min), worker count (2) | `app/config.py` |
| Port (8000) | `main.py` |

The server deliberately listens on `127.0.0.1` only. If you want to expose it to the
network, you first need to add authentication, access control and tighter resource limits;
otherwise anyone on the network can make requests to any address through your machine.

The UI loads its fonts from Google Fonts, so even though the download itself happens
locally, a request goes to Google when the page opens.

There is currently no CI workflow and no Docker image in the repo.

## Note

Use it only for content that belongs to you or that you are allowed to download. Following
the platforms' terms of service and copyright rules is your responsibility.

## License

[MIT](LICENSE)
