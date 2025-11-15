"""Base download strategy."""

from abc import ABC, abstractmethod
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BaseDownloadStrategy(ABC):
    """Abstract base class for download strategies."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this download method is available.

        Returns:
            True if downloader is available on system
        """
        pass

    @abstractmethod
    def download(self, url: str, output_path: Path) -> bool:
        """Download file from URL to output path.

        Args:
            url: URL to download
            output_path: Path to save file

        Returns:
            True if download succeeded
        """
        pass

    def get_name(self) -> str:
        """Get strategy name.

        Returns:
            Strategy name
        """
        return self.__class__.__name__
