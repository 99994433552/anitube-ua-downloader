"""Base classes for video URL extraction."""

from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class BaseVideoExtractor(ABC):
    """Abstract base class for video URL extractors."""

    @abstractmethod
    def can_handle(self, html: str) -> bool:
        """Check if this extractor can handle the given HTML.

        Args:
            html: HTML content from player iframe

        Returns:
            True if this extractor can handle the content
        """
        pass

    @abstractmethod
    def extract_url(self, html: str) -> Optional[str]:
        """Extract video URL from HTML.

        Args:
            html: HTML content from player iframe

        Returns:
            Extracted URL or None if not found
        """
        pass

    def normalize_url(self, url: str) -> str:
        """Normalize URL (add protocol, remove trailing slash).

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        if not url:
            return url

        # Add https if URL starts with //
        if url.startswith("//"):
            url = "https:" + url

        # Remove trailing slash
        url = url.rstrip("/")

        return url
