"""M3U8 URL extractor module."""

import re
import logging
from typing import Optional
import requests

from ..models import Episode
from .base_extractor import BaseVideoExtractor
from .tortuga_extractor import TortugaCoreExtractor
from .playerjs_extractor import PlayerJSExtractor

logger = logging.getLogger(__name__)


class M3U8Extractor:
    """Extractor for m3u8 URLs from video player pages."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        extractors: Optional[list[BaseVideoExtractor]] = None,
    ):
        """Initialize extractor.

        Args:
            session: HTTP session
            extractors: List of video extractors to try in order
        """
        self.session = session or self._create_default_session()
        self.extractors = extractors or [
            TortugaCoreExtractor(),  # Try newer player first
            PlayerJSExtractor(),  # Fallback to older player
        ]

    def _create_default_session(self) -> requests.Session:
        """Create default HTTP session."""
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36",
            }
        )
        return session

    def _select_best_quality(self, file_value: str) -> str:
        """Extract best quality URL from multi-quality file string.

        Format: [360p]url1,[720p]url2,[1080p]url3
        Returns the highest quality URL available.

        Args:
            file_value: File value that may contain multiple quality options

        Returns:
            URL of the best quality
        """
        if not file_value:
            return file_value

        # Check if this is multi-quality format
        if "[" not in file_value or "]" not in file_value:
            return file_value

        # Parse quality options: [360p]url,[720p]url,[1080p]url
        quality_pattern = r"\[(\d+)p\]([^,\[\]]+)"
        matches = re.findall(quality_pattern, file_value)

        if not matches:
            return file_value

        # Sort by quality (descending) and pick highest
        sorted_qualities = sorted(matches, key=lambda x: int(x[0]), reverse=True)
        best_quality, best_url = sorted_qualities[0]

        # Remove trailing slash if present
        best_url = best_url.rstrip("/")

        logger.info(f"Selected {best_quality}p quality from available options")
        return best_url

    def _extract_from_html(self, html: str) -> Optional[str]:
        """Try extractors in order until one succeeds.

        Args:
            html: HTML content

        Returns:
            Extracted URL or None if all extractors fail
        """
        for extractor in self.extractors:
            if not extractor.can_handle(html):
                logger.debug(
                    f"{extractor.__class__.__name__} cannot handle this content"
                )
                continue

            url = extractor.extract_url(html)
            if url:
                logger.info(
                    f"Successfully extracted URL using {extractor.__class__.__name__}"
                )
                return url

        logger.warning("No extractor could extract URL")
        return None

    def extract_m3u8_url(self, episode: Episode) -> Optional[str]:
        """Extract m3u8 URL from episode's data_file iframe.

        Args:
            episode: Episode to extract URL for

        Returns:
            Extracted m3u8 URL or None
        """
        if not episode.data_file:
            logger.warning(f"Episode {episode.number} has no data_file URL")
            return None

        try:
            # Fetch iframe page with proper Referer
            headers = {
                "Referer": "https://anitube.in.ua/",
            }
            response = self.session.get(episode.data_file, headers=headers)
            response.raise_for_status()
            html = response.text

            # Check if response is valid
            if not html or len(html) < 100:
                logger.error(
                    f"Empty or too short response for episode {episode.number} "
                    f"(got {len(html)} bytes)"
                )
                return None

            # Extract URL using extractors
            m3u8_url = self._extract_from_html(html)

            if not m3u8_url:
                logger.warning(f"Could not extract URL for episode {episode.number}")
                return None

            # Select best quality if multi-quality format
            m3u8_url = self._select_best_quality(m3u8_url)

            logger.info(f"Extracted m3u8 URL for episode {episode.number}: {m3u8_url}")
            return m3u8_url

        except Exception as e:
            logger.error(f"Failed to extract URL for episode {episode.number}: {e}")
            return None

    def extract_all_m3u8_urls(self, episodes: list[Episode]) -> list[Episode]:
        """Extract m3u8 URLs for all episodes.

        Args:
            episodes: List of episodes

        Returns:
            List of episodes with m3u8_url populated
        """
        logger.info(f"Extracting m3u8 URLs for {len(episodes)} episodes")

        for episode in episodes:
            m3u8_url = self.extract_m3u8_url(episode)
            episode.m3u8_url = m3u8_url

        successful = sum(1 for ep in episodes if ep.m3u8_url)
        logger.info(f"Successfully extracted {successful}/{len(episodes)} URLs")

        return episodes
