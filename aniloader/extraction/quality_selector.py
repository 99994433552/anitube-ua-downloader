"""Quality selector for multi-quality URLs."""

import re
import logging

logger = logging.getLogger(__name__)


class QualitySelector:
    """Selector for best quality from multi-quality URLs."""

    def select_best_quality(self, file_value: str) -> str:
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
