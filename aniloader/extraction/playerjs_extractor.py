"""PlayerJS player extractor."""

import re
import json
import logging
from typing import Optional

from .base_extractor import BaseVideoExtractor

logger = logging.getLogger(__name__)


class PlayerJSExtractor(BaseVideoExtractor):
    """Extractor for PlayerJS player."""

    def can_handle(self, html: str) -> bool:
        """Check if HTML contains PlayerJS."""
        return "Playerjs" in html

    def extract_url(self, html: str) -> Optional[str]:
        """Extract m3u8 URL from PlayerJS configuration.

        Args:
            html: HTML content

        Returns:
            Extracted m3u8 URL or None
        """
        # Pattern: Playerjs({...})
        pattern = r"Playerjs\s*\(\s*(\{[^}]+\})\s*\)"
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            # Try alternative pattern with more content
            pattern = r"Playerjs\s*\(\s*(\{[\s\S]*?\})\s*\)"
            match = re.search(pattern, html)

        if not match:
            logger.debug("No PlayerJS configuration found")
            return None

        json_str = match.group(1)

        # PlayerJS often uses single quotes instead of double quotes
        # Replace single quotes with double quotes for valid JSON
        json_str_cleaned = json_str.replace("'", '"')

        try:
            # Try parsing as JSON
            config = json.loads(json_str_cleaned)
            file_value = config.get("file", "")

            if not file_value:
                logger.warning("PlayerJS config has no 'file' field")
                return None

            # Normalize URL
            m3u8_url = self.normalize_url(file_value)

            logger.info(f"Extracted URL from PlayerJS: {m3u8_url}")
            return m3u8_url

        except json.JSONDecodeError as e:
            # Fallback: use regex to extract file value directly
            logger.debug(f"JSON parsing failed ({e}), using regex fallback")
            file_match = re.search(r'file["\']?\s*:\s*["\']([^"\']+)["\']', json_str)
            if file_match:
                m3u8_url = file_match.group(1)
                m3u8_url = self.normalize_url(m3u8_url)
                logger.info(f"Extracted URL via regex: {m3u8_url}")
                return m3u8_url

            logger.error("Failed to extract file from PlayerJS config")
            return None
