"""Protocol definitions for dependency inversion (SOLID DIP principle)."""

from pathlib import Path
from typing import Protocol, Optional
import requests
from bs4 import BeautifulSoup

from .models import Anime, Episode, Voice, Player


class HTTPClientProtocol(Protocol):
    """Protocol for HTTP client operations."""

    @property
    def session(self) -> requests.Session:
        """Get the underlying requests session."""
        ...

    def get(self, url: str, **kwargs) -> requests.Response:
        """Perform GET request."""
        ...

    def post(self, url: str, **kwargs) -> requests.Response:
        """Perform POST request."""
        ...


class HTMLParserProtocol(Protocol):
    """Protocol for HTML parsing operations."""

    def parse_voice_items(self, html: str) -> list[dict[str, str | int]]:
        """Parse voice items from playlist HTML."""
        ...

    def parse_episode_items(
        self, html: str, player_id: str
    ) -> list[dict[str, str | int]]:
        """Parse episode items for a specific player."""
        ...

    def parse_soup(self, html: str) -> BeautifulSoup:
        """Parse HTML string to BeautifulSoup object."""
        ...


class MetadataExtractorProtocol(Protocol):
    """Protocol for metadata extraction operations."""

    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extract English title from page."""
        ...

    def extract_season(self, title: str) -> int:
        """Extract season number from title."""
        ...

    def extract_year(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract release year from page."""
        ...

    def extract_news_id(self, url: str) -> str:
        """Extract news ID from URL."""
        ...

    def extract_user_hash(self, html: str) -> str:
        """Extract user hash from HTML."""
        ...


class ContentTypeDetectorProtocol(Protocol):
    """Protocol for content type detection (movie vs series)."""

    def detect_is_movie(
        self,
        episode_items: list[dict[str, str | int]],
        all_items: list[dict[str, str | int]],
    ) -> bool:
        """Determine if content is a movie or series."""
        ...


class ScraperProtocol(Protocol):
    """Protocol for anime scraper operations."""

    def fetch_anime_metadata(self, url: str) -> Anime:
        """Fetch anime metadata from URL."""
        ...

    def get_available_players(self, anime: Anime, voice_id: str) -> list[Player]:
        """Get available players for a voice."""
        ...


class VideoExtractorProtocol(Protocol):
    """Protocol for video URL extraction."""

    def can_handle(self, html: str) -> bool:
        """Check if this extractor can handle the given HTML."""
        ...

    def extract_url(self, html: str) -> Optional[str]:
        """Extract m3u8 URL from HTML."""
        ...


class M3U8ExtractorProtocol(Protocol):
    """Protocol for M3U8 URL extraction from episodes."""

    def extract_m3u8_url(self, episode: Episode) -> Optional[str]:
        """Extract m3u8 URL for a single episode."""
        ...

    def extract_all_m3u8_urls(self, episodes: list[Episode]) -> list[Episode]:
        """Extract m3u8 URLs for all episodes."""
        ...


class DownloadStrategyProtocol(Protocol):
    """Protocol for download strategy."""

    def is_available(self) -> bool:
        """Check if this download strategy is available."""
        ...

    def download(self, url: str, output_path: Path) -> bool:
        """Download file from URL to output path."""
        ...


class FilenameGeneratorProtocol(Protocol):
    """Protocol for filename generation."""

    def generate_episode_filename(self, anime: Anime, episode: Episode) -> str:
        """Generate filename for an episode."""
        ...


class FileSystemManagerProtocol(Protocol):
    """Protocol for filesystem operations."""

    def create_output_directory(self, anime: Anime, base_dir: str) -> Path:
        """Create and return output directory for anime."""
        ...

    def file_exists(self, path: Path) -> bool:
        """Check if file exists."""
        ...


class DownloaderProtocol(Protocol):
    """Protocol for video downloader."""

    def download_episode(
        self,
        anime: Anime,
        episode: Episode,
        output_dir: Path,
    ) -> tuple[bool, str]:
        """Download a single episode."""
        ...


class InteractiveSelectorProtocol(Protocol):
    """Protocol for interactive selection UI."""

    def select_voice(self, voices: list[Voice]) -> Voice:
        """Let user select a voice interactively."""
        ...

    def select_player(self, players: list[Player]) -> Player:
        """Let user select a player interactively."""
        ...


class OrchestratorProtocol(Protocol):
    """Protocol for download orchestration."""

    def run(
        self,
        url: str,
        voice_index: Optional[int] = None,
        title: Optional[str] = None,
        output_dir: str = ".",
    ) -> dict[str, int]:
        """Run the download process and return statistics."""
        ...
