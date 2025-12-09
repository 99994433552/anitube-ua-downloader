"""Video downloader module."""

import logging
from pathlib import Path
from typing import Optional

from ..models import Anime, Episode
from .strategies.base_strategy import BaseDownloadStrategy
from .strategies.ytdlp_strategy import YtDlpStrategy
from .filesystem import FileSystemManager

logger = logging.getLogger(__name__)


class VideoDownloader:
    """Video downloader with configurable strategy."""

    def __init__(
        self,
        download_strategy: Optional[BaseDownloadStrategy] = None,
        fs_manager: Optional[FileSystemManager] = None,
    ):
        """Initialize downloader.

        Args:
            download_strategy: Strategy for downloading files
            fs_manager: Filesystem manager
        """
        self.download_strategy = download_strategy or YtDlpStrategy(
            use_aria2c_downloader=True
        )
        self.fs_manager = fs_manager or FileSystemManager()

    def download_episode(
        self,
        anime: Anime,
        episode: Episode,
        output_dir: Path,
    ) -> tuple[bool, str]:
        """Download a single episode.

        Args:
            anime: Anime object
            episode: Episode to download
            output_dir: Output directory

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not episode.m3u8_url:
            msg = f"Episode {episode.number} has no m3u8_url"
            logger.warning(msg)
            return False, msg

        # Generate filename
        filename = self.fs_manager.generate_episode_filename(anime, episode)
        output_path = output_dir / filename

        # Check if already exists
        if self.fs_manager.file_exists(output_path):
            msg = f"Skipping episode {episode.number} (already exists)"
            logger.info(msg)
            return True, msg

        # Download
        logger.info(f"Downloading episode {episode.number}: {filename}")

        try:
            success = self.download_strategy.download(episode.m3u8_url, output_path)

            if success:
                msg = f"Successfully downloaded episode {episode.number}"
                logger.info(msg)
                return True, msg
            else:
                msg = f"Failed to download episode {episode.number}"
                logger.error(msg)
                return False, msg

        except Exception as e:
            msg = f"Error downloading episode {episode.number}: {e}"
            logger.error(msg)
            return False, msg

    def create_output_directory(self, anime: Anime, base_dir: str) -> Path:
        """Create output directory for anime.

        Args:
            anime: Anime object
            base_dir: Base directory

        Returns:
            Created directory path
        """
        return self.fs_manager.create_output_directory(anime, base_dir)
