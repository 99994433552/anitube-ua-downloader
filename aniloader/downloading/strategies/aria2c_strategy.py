"""Aria2c download strategy for direct file downloads."""

import subprocess
import shutil
from pathlib import Path
import logging

from .base_strategy import BaseDownloadStrategy

logger = logging.getLogger(__name__)


class Aria2cStrategy(BaseDownloadStrategy):
    """Download strategy using aria2c for direct file downloads."""

    def is_available(self) -> bool:
        """Check if aria2c is available."""
        return shutil.which("aria2c") is not None

    def download(self, url: str, output_path: Path) -> bool:
        """Download file using aria2c.

        Args:
            url: Direct file URL (not m3u8)
            output_path: Path to save file

        Returns:
            True if download succeeded
        """
        if not self.is_available():
            logger.warning("aria2c not available")
            return False

        try:
            cmd = [
                "aria2c",
                "--min-split-size=1M",
                "--max-connection-per-server=16",
                "--split=16",
                "--continue=true",
                "--max-tries=5",
                "--retry-wait=3",
                "--out",
                str(output_path),
                url,
            ]

            logger.info(f"Downloading with aria2c: {url}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                logger.info(f"Downloaded successfully: {output_path}")
                return True
            else:
                logger.error(f"aria2c failed: {result.stderr}")
                return False
        except OSError as e:
            logger.error(f"Failed to run aria2c: {e}")
            return False
