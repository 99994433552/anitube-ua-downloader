"""Aniloader - Automated anime downloader for anitube.in.ua."""

from .models import Anime, Episode, Voice, Player, DownloadConfig
from .exceptions import (
    AniloaderError,
    NoVoicesError,
    NoPlayersError,
    UserCancelledError,
    ExtractionError,
    DownloadError,
)
from .scraper_refactored import AnitubeScraper
from .factories.component_factory import ComponentFactory

__all__ = [
    # Models
    "Anime",
    "Episode",
    "Voice",
    "Player",
    "DownloadConfig",
    # Exceptions
    "AniloaderError",
    "NoVoicesError",
    "NoPlayersError",
    "UserCancelledError",
    "ExtractionError",
    "DownloadError",
    # Main classes
    "AnitubeScraper",
    "ComponentFactory",
]

__version__ = "0.1.0"
