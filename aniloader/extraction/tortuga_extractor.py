"""TortugaCore player extractor."""

import re
import base64
import logging
from typing import Optional

from .base_extractor import BaseVideoExtractor

logger = logging.getLogger(__name__)


class TortugaCoreExtractor(BaseVideoExtractor):
    """Extractor for TortugaCore player."""

    def can_handle(self, html: str) -> bool:
        """Check if HTML contains TortugaCore player."""
        return "TortugaCore" in html

    def extract_url(self, html: str) -> Optional[str]:
        """Extract m3u8 URL from TortugaCore player.

        TortugaCore encodes URLs as base64 + reversed string.

        Args:
            html: HTML content

        Returns:
            Decoded m3u8 URL or None
        """
        # Pattern: new TortugaCore({ ... file: "base64encoded" ... })
        pattern = r'new\s+TortugaCore\s*\(\s*\{[^}]*file\s*:\s*["\']([^"\']+)["\']'
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            logger.debug("No TortugaCore file pattern found")
            return None

        encoded_file = match.group(1)

        try:
            # Decode: base64 decode -> reverse string
            decoded = base64.b64decode(encoded_file).decode("utf-8")
            m3u8_url = decoded[::-1]  # Reverse the string

            # Normalize URL
            m3u8_url = self.normalize_url(m3u8_url)

            logger.info(f"Extracted URL from TortugaCore: {m3u8_url}")
            return m3u8_url
        except (ValueError, UnicodeDecodeError) as e:
            # ValueError covers base64.binascii.Error (it's a subclass)
            logger.warning(f"Failed to decode TortugaCore file: {e}")
            return None
