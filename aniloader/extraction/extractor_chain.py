"""Chain of Responsibility for video extractors."""

import logging
from typing import Optional

from .base_extractor import BaseVideoExtractor

logger = logging.getLogger(__name__)


class ExtractorChain:
    """Chain of Responsibility pattern for trying multiple extractors."""

    def __init__(self, extractors: list[BaseVideoExtractor]):
        """Initialize chain with list of extractors.

        Args:
            extractors: List of extractors to try in order
        """
        self.extractors = extractors

    def extract(self, html: str) -> Optional[str]:
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

        logger.warning("No extractor in chain could extract URL")
        return None

    def add_extractor(self, extractor: BaseVideoExtractor) -> None:
        """Add extractor to the chain.

        Args:
            extractor: Extractor to add
        """
        self.extractors.append(extractor)
