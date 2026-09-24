from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field


class InfoRequest(BaseModel):
    url: AnyHttpUrl


class DownloadRequest(BaseModel):
    url: AnyHttpUrl
    format: Literal["mp4", "mp3"] = Field(default="mp4")
