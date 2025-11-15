"""Refactored anime scraper using SOLID principles."""

import json
import logging
from typing import Optional

from .models import Anime, Episode, Player, Voice
from .core.http_client import HTTPClient
from .parsing.html_parser import HTMLParser
from .parsing.metadata_extractor import MetadataExtractor
from .parsing.content_detector import ContentTypeDetector
from .parsing.voice_extractor import VoiceExtractor
from .parsing.episode_extractor import EpisodeExtractor

logger = logging.getLogger(__name__)


class AnitubeScraper:
    """Refactored scraper with dependency injection and SOLID principles."""

    def __init__(
        self,
        http_client: Optional[HTTPClient] = None,
        html_parser: Optional[HTMLParser] = None,
        metadata_extractor: Optional[MetadataExtractor] = None,
        content_detector: Optional[ContentTypeDetector] = None,
        voice_extractor: Optional[VoiceExtractor] = None,
        episode_extractor: Optional[EpisodeExtractor] = None,
    ):
        """Initialize scraper with dependency injection.

        Args:
            http_client: HTTP client for requests
            html_parser: HTML parser
            metadata_extractor: Metadata extractor
            content_detector: Content type detector
            voice_extractor: Voice extractor
            episode_extractor: Episode extractor
        """
        # Use provided components or create defaults
        self.http_client = http_client or HTTPClient()
        self.html_parser = html_parser or HTMLParser()
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        self.content_detector = content_detector or ContentTypeDetector()
        self.voice_extractor = voice_extractor or VoiceExtractor()
        self.episode_extractor = episode_extractor or EpisodeExtractor()

        # Internal state
        self._anime_url: Optional[str] = None
        self._playlist_html: str = ""
        self._user_hash: str = ""
        self._all_items: list[dict[str, str | int]] = []

    @property
    def session(self):
        """Get HTTP session for compatibility."""
        return self.http_client.session

    def fetch_anime_metadata(self, url: str) -> Anime:
        """Fetch anime metadata from main page.

        Args:
            url: Anime page URL

        Returns:
            Anime object with basic metadata
        """
        self._anime_url = url
        response = self.http_client.get(url)
        soup = self.html_parser.parse_soup(response.text)

        # Extract metadata
        news_id = self.metadata_extractor.extract_news_id(url)
        title_en = self.metadata_extractor.extract_title(soup)
        season = self.metadata_extractor.extract_season(title_en)
        year = self.metadata_extractor.extract_year(soup)
        self._user_hash = self.metadata_extractor.extract_user_hash(response.text)

        # Get base title without season number
        base_title = self.metadata_extractor.get_base_title(title_en)

        logger.info(f"Fetched metadata: {title_en} (Season {season}, Year {year})")

        anime = Anime(
            news_id=news_id,
            title_en=base_title,
            year=year,
            season=season,
        )

        # Fetch playlist to populate voices
        return self.fetch_playlist(anime)

    def fetch_playlist(
        self,
        anime: Anime,
        voice_id: Optional[str] = None,
        player_id: Optional[str] = None,
    ) -> Anime:
        """Fetch playlist with episodes via AJAX.

        Args:
            anime: Anime object to populate
            voice_id: Optional voice ID to filter
            player_id: Optional player ID to filter

        Returns:
            Updated Anime object with voices and episodes
        """
        if not self._anime_url:
            raise ValueError("anime_url not set. Call fetch_anime_metadata first.")

        # Make AJAX request
        try:
            html_content = self.http_client.ajax_playlist_request(
                news_id=anime.news_id,
                user_hash=self._user_hash,
                referer=self._anime_url,
            )

            # Try to parse as JSON (new format)
            try:
                data = json.loads(html_content)
                html_content = data.get("response", "")

                if not data.get("success", True) or not html_content:
                    logger.info("AJAX playlist not available, using fallback")
                    return self._parse_embedded_iframe(anime)
            except json.JSONDecodeError:
                # Response is plain HTML
                pass

        except Exception as e:
            logger.error(f"Failed to fetch playlist: {e}")
            return anime

        self._playlist_html = html_content

        # Parse voice/player items
        self._all_items = self.html_parser.parse_voice_items(html_content)

        if not self._all_items:
            logger.warning("No voice/player items found")
            return anime

        # Get episode information for content type detection
        episode_texts = self.html_parser.get_episode_texts(html_content)
        unique_files = self.html_parser.get_unique_episode_files(html_content)

        # Detect content type
        is_movie = self.content_detector.detect_is_movie(
            episode_texts=episode_texts,
            unique_files_count=len(unique_files),
            total_items_count=len(self._all_items),
        )
        anime.is_movie = is_movie

        # Extract voices
        max_depth = self.html_parser.get_max_depth(self._all_items)
        voices = self.voice_extractor.extract_voices(
            all_items=self._all_items,
            is_movie=is_movie,
            max_depth=max_depth,
        )
        anime.voices = voices

        # If voice_id not specified, use first voice for initial extraction
        if not voice_id and voices:
            voice_id = voices[0].id

        # Parse episode items
        episode_items_raw = []
        if voice_id:
            # We need to convert HTML parser output to expected format
            episode_items_raw = self.html_parser.parse_episode_items(
                html_content, voice_id
            )

        # Extract episodes
        episodes = self.episode_extractor.extract_episodes(
            episode_items=episode_items_raw,
            voice_id=voice_id or "",
            player_id=player_id,
            is_movie=is_movie,
            all_items=self._all_items,
        )
        anime.episodes = episodes

        logger.info(
            f"Fetched playlist: {len(voices)} voices, "
            f"{len(episodes)} episodes, "
            f"type={'movie' if is_movie else 'series'}"
        )

        return anime

    def get_available_players(self, anime: Anime, voice_id: str) -> list[Player]:
        """Get available players for a specific voice.

        Args:
            anime: Anime object
            voice_id: Voice ID to get players for

        Returns:
            List of available players
        """
        if not self._all_items:
            # Need to fetch playlist first
            logger.debug("Fetching playlist to get player options")
            self.fetch_playlist(anime)

        players = self.voice_extractor.extract_players_for_voice(
            all_items=self._all_items,
            voice_id=voice_id,
        )

        return players

    def _parse_embedded_iframe(self, anime: Anime) -> Anime:
        """Fallback parser for old format pages with embedded iframe.

        Args:
            anime: Anime object to populate

        Returns:
            Updated Anime object
        """
        logger.info("Using embedded iframe fallback")

        if not self._anime_url:
            logger.error("Cannot parse embedded iframe: anime_url not set")
            anime.is_movie = True
            anime.voices = []
            anime.episodes = []
            return anime

        # Fetch the original page HTML
        response = self.http_client.get(self._anime_url)

        # Find embedded iframe using HTMLParser
        iframe_url = self.html_parser.find_embedded_iframe(response.text)

        if not iframe_url:
            logger.error("No embedded iframe found on page")
            anime.is_movie = True
            anime.voices = []
            anime.episodes = []
            return anime

        # For old format: single iframe = single voice/player = movie
        anime.is_movie = True
        anime.voices = [Voice(id="0", name="Єдина озвучка")]

        # Create single episode (movie)
        anime.episodes = [
            Episode(
                number=1,
                data_id="0",
                data_file=iframe_url,
            )
        ]
        anime.total_episodes = 1

        logger.info(f"Parsed embedded iframe: {iframe_url}")

        return anime
