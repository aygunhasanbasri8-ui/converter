from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field


class InfoRequest(BaseModel):
    url: AnyHttpUrl


class DownloadRequest(BaseModel):
    url: AnyHttpUrl
    format: Literal["mp4", "mp3"] = Field(default="mp4")
    # MP4 için en yüksek çözünürlük (piksel yükseklik); boşsa en iyisi. MP3'te yok sayılır.
    quality: int | None = Field(default=None, ge=144, le=4320)
