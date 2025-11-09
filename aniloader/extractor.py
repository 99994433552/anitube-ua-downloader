"""M3U8 URL extractor from video player iframes."""

import re
import json
import base64
import logging
from typing import Optional

import requests

from .models import Episode

logger = logging.getLogger(__name__)


class M3U8Extractor:
    """Extract m3u8 URLs from Playerjs and TortugaCore embedded players."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36",
        })

    def _extract_tortuga_url(self, html: str) -> Optional[str]:
        """Extract m3u8 URL from TortugaCore player."""
        # Pattern: new TortugaCore({ ... file: "base64encoded" ... })
        pattern = r'new\s+TortugaCore\s*\(\s*\{[^}]*file\s*:\s*["\']([^"\']+)["\']'
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            return None

        encoded_file = match.group(1)

        try:
            # Decode: base64 decode -> reverse string
            decoded = base64.b64decode(encoded_file).decode('utf-8')
            m3u8_url = decoded[::-1]  # Reverse the string
            return m3u8_url
        except Exception as e:
            logger.error(f"Failed to decode TortugaCore file: {e}")
            return None

    def extract_m3u8_url(self, episode: Episode) -> Optional[str]:
        """Extract m3u8 URL from episode's data_file iframe."""
        if not episode.data_file:
            logger.warning(
                f"Episode {episode.number} has no data_file URL"
            )
            return None

        try:
            # Fetch iframe page
            response = self.session.get(episode.data_file)
            response.raise_for_status()
            html = response.text

            # Try TortugaCore first (newer player)
            m3u8_url = self._extract_tortuga_url(html)
            if m3u8_url:
                logger.info(
                    f"Extracted m3u8 URL from TortugaCore for episode "
                    f"{episode.number}: {m3u8_url}"
                )
                return m3u8_url

            # Fallback to Playerjs
            # Pattern: Playerjs({...})
            pattern = r'Playerjs\s*\(\s*(\{[^}]+\})\s*\)'
            match = re.search(pattern, html, re.DOTALL)

            if not match:
                # Try alternative pattern with more content
                pattern = r'Playerjs\s*\(\s*(\{[\s\S]*?\})\s*\)'
                match = re.search(pattern, html)

            if not match:
                logger.error(
                    f"Could not find Playerjs or TortugaCore config for "
                    f"episode {episode.number}"
                )
                return None

            # Extract and parse JSON
            json_str = match.group(1)

            # Clean up JSON string
            # Replace single quotes with double quotes for JSON compatibility
            json_str_cleaned = json_str.replace("'", '"')
            # Remove trailing commas
            json_str_cleaned = re.sub(r',(\s*[}\]])', r'\1', json_str_cleaned)

            try:
                config = json.loads(json_str_cleaned)
            except json.JSONDecodeError:
                # Try to extract just the file field with regex
                # Try both single and double quotes
                file_match = re.search(
                    r'file\s*:\s*["\']([^"\']+)["\']',
                    json_str
                )
                if file_match:
                    return file_match.group(1)

                logger.error(
                    f"Could not parse Playerjs JSON for episode "
                    f"{episode.number}: {json_str[:100]}..."
                )
                return None

            # Extract file URL (this is the m3u8 URL)
            m3u8_url = config.get('file')

            if not m3u8_url:
                logger.error(
                    f"No 'file' field in Playerjs config for episode "
                    f"{episode.number}"
                )
                return None

            # Sometimes the URL needs the base domain prepended
            if m3u8_url.startswith('//'):
                m3u8_url = 'https:' + m3u8_url
            elif m3u8_url.startswith('/'):
                # Extract base URL from data_file
                base_url = re.match(
                    r'(https?://[^/]+)',
                    episode.data_file
                )
                if base_url:
                    m3u8_url = base_url.group(1) + m3u8_url

            logger.info(
                f"Extracted m3u8 URL for episode {episode.number}: "
                f"{m3u8_url}"
            )

            return m3u8_url

        except requests.RequestException as e:
            logger.error(
                f"Failed to fetch iframe for episode {episode.number}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error extracting m3u8 for episode "
                f"{episode.number}: {e}"
            )
            return None

    def extract_all_m3u8_urls(self, episodes: list[Episode]) -> list[Episode]:
        """Extract m3u8 URLs for all episodes."""
        for episode in episodes:
            m3u8_url = self.extract_m3u8_url(episode)
            if m3u8_url:
                episode.m3u8_url = m3u8_url

        return episodes
