"""Refactored M3U8 extractor using SOLID principles."""

import logging
from typing import Optional
import requests

from ..models import Episode
from .extractor_chain import ExtractorChain
from .quality_selector import QualitySelector
from .tortuga_extractor import TortugaCoreExtractor
from .playerjs_extractor import PlayerJSExtractor

logger = logging.getLogger(__name__)


class M3U8Extractor:
    """Refactored M3U8 extractor with dependency injection."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        extractor_chain: Optional[ExtractorChain] = None,
        quality_selector: Optional[QualitySelector] = None,
    ):
        """Initialize extractor with dependencies.

        Args:
            session: HTTP session
            extractor_chain: Chain of video extractors
            quality_selector: Quality selector for multi-quality URLs
        """
        self.session = session or self._create_default_session()
        self.quality_selector = quality_selector or QualitySelector()

        # Create default extractor chain if not provided
        if extractor_chain is None:
            extractors = [
                TortugaCoreExtractor(),  # Try newer player first
                PlayerJSExtractor(),  # Fallback to older player
            ]
            self.extractor_chain = ExtractorChain(extractors)
        else:
            self.extractor_chain = extractor_chain

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

            # Extract URL using chain of extractors
            m3u8_url = self.extractor_chain.extract(html)

            if not m3u8_url:
                logger.warning(f"Could not extract URL for episode {episode.number}")
                return None

            # Select best quality if multi-quality format
            m3u8_url = self.quality_selector.select_best_quality(m3u8_url)

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
