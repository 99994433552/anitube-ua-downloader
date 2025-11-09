"""Pydantic models for anime data structures."""

from pydantic import BaseModel, Field


class Voice(BaseModel):
    """Represents a voice/dub option for anime."""

    id: str = Field(..., description="Voice ID from data-id attribute")
    name: str = Field(..., description="Voice name (e.g., 'Original', 'Ukrainian')")


class Player(BaseModel):
    """Represents a player option for a voice."""

    id: str = Field(..., description="Player ID from data-id attribute")
    name: str = Field(..., description="Player name (e.g., 'ASHDI', 'TRG')")


class Episode(BaseModel):
    """Represents a single anime episode."""

    number: int = Field(..., description="Episode number")
    data_id: str = Field(..., description="Episode ID from data-id attribute")
    data_file: str = Field(..., description="URL to iframe with video player")
    m3u8_url: str | None = Field(
        default=None,
        description="Extracted m3u8 URL for downloading"
    )


class Anime(BaseModel):
    """Represents anime series metadata."""

    news_id: str = Field(..., description="Anime ID from URL")
    title_en: str = Field(..., description="English title")
    year: int | None = Field(default=None, description="Release year")
    total_episodes: int | None = Field(
        default=None,
        description="Total number of episodes"
    )
    voices: list[Voice] = Field(
        default_factory=list,
        description="Available voice options"
    )
    episodes: list[Episode] = Field(
        default_factory=list,
        description="List of episodes"
    )


class DownloadConfig(BaseModel):
    """Configuration for downloading episodes."""

    anime_url: str = Field(..., description="URL to anime page")
    output_dir: str = Field(
        default=".",
        description="Directory to save downloaded episodes"
    )
    voice_id: str | None = Field(
        default=None,
        description="Selected voice ID"
    )
    use_aria2c: bool = Field(
        default=True,
        description="Use aria2c for faster downloads"
    )
