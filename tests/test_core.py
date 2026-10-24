import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.downloader import _find_output, _first_entry
from app.errors import readable_error
from app.jobs import JobStore


class DownloaderTests(unittest.TestCase):
    def test_first_entry_handles_playlist_data(self) -> None:
        data = {"entries": [{"title": "Example"}]}

        self.assertEqual(_first_entry(data), {"title": "Example"})

    def test_find_output_prefers_requested_format(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "video.webm").write_bytes(b"larger")
            (target / "video.mp4").write_bytes(b"small")

            output = _find_output(target, "mp4")

            self.assertEqual(output, target / "video.mp4")


class JobStoreTests(unittest.TestCase):
    def test_created_job_can_be_updated_and_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with ThreadPoolExecutor(max_workers=1) as executor:
                store = JobStore(Path(directory), executor, ttl_seconds=3600)
                store.create("job", "mp4")
                store.update("job", state="ready", filename="video.mp4")

                job = store.get("job")

        self.assertIsNotNone(job)
        self.assertEqual(job["state"], "ready")
        self.assertEqual(job["filename"], "video.mp4")


class ErrorTests(unittest.TestCase):
    def test_known_downloader_errors_are_user_facing(self) -> None:
        message = readable_error(RuntimeError("ffmpeg executable not found"))

        self.assertIn("ffmpeg", message)
        self.assertNotIn("Traceback", message)


if __name__ == "__main__":
    unittest.main()
