"""Aniloader - Automated anime downloader for anitube.in.ua."""

from .models import Anime, Episode, Voice, Player
from .exceptions import (
    AniloaderError,
    NoVoicesError,
    NoPlayersError,
    UserCancelledError,
    ExtractionError,
    DownloadError,
)
from .scraper_refactored import AnitubeScraper
from .factories.component_factory import create_orchestrator

__all__ = [
    # Models
    "Anime",
    "Episode",
    "Voice",
    "Player",
    # Exceptions
    "AniloaderError",
    "NoVoicesError",
    "NoPlayersError",
    "UserCancelledError",
    "ExtractionError",
    "DownloadError",
    # Main classes
    "AnitubeScraper",
    "create_orchestrator",
]

__version__ = "0.1.0"
