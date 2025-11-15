"""yt-dlp download strategy for HLS/m3u8 streams."""

import subprocess
import shutil
from pathlib import Path
import logging

from .base_strategy import BaseDownloadStrategy

logger = logging.getLogger(__name__)


class YtDlpStrategy(BaseDownloadStrategy):
    """Download strategy using yt-dlp for HLS streams."""

    def __init__(self, use_aria2c_downloader: bool = True):
        """Initialize strategy.

        Args:
            use_aria2c_downloader: Whether to use aria2c as yt-dlp's downloader
        """
        self.use_aria2c_downloader = use_aria2c_downloader

    def is_available(self) -> bool:
        """Check if yt-dlp is available."""
        return shutil.which("yt-dlp") is not None

    def download(self, url: str, output_path: Path) -> bool:
        """Download HLS stream using yt-dlp.

        Args:
            url: m3u8 URL
            output_path: Path to save file

        Returns:
            True if download succeeded
        """
        if not self.is_available():
            logger.error("yt-dlp not available")
            return False

        try:
            cmd = [
                "yt-dlp",
                "--no-check-certificate",
                "-f",
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--merge-output-format",
                "mp4",
                "--concurrent-fragments",
                "16",
            ]

            # Use aria2c as downloader if available
            if self.use_aria2c_downloader and shutil.which("aria2c"):
                cmd.extend(
                    [
                        "--downloader",
                        "aria2c",
                        "--downloader-args",
                        "aria2c:--min-split-size=1M --max-connection-per-server=16 --split=16",
                    ]
                )

            cmd.extend(["-o", str(output_path), url])

            logger.info(f"Downloading with yt-dlp: {url}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Downloaded successfully: {output_path}")
                return True
            else:
                logger.error(f"yt-dlp failed: {result.stderr}")
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"yt-dlp download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during yt-dlp download: {e}")
            return False
