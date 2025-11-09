"""Video downloader using yt-dlp with aria2c acceleration."""

import os
import subprocess
import logging
import shutil
from pathlib import Path
from typing import Optional

from .models import Anime, Episode

logger = logging.getLogger(__name__)


class VideoDownloader:
    """Download episodes using yt-dlp with optimizations."""

    def __init__(self, use_aria2c: bool = True):
        self.use_aria2c = use_aria2c and self._check_aria2c_available()

        if use_aria2c and not self.use_aria2c:
            logger.warning(
                "aria2c not found, falling back to default downloader. "
                "Install aria2c for faster downloads: brew install aria2"
            )

    def _check_aria2c_available(self) -> bool:
        """Check if aria2c is installed."""
        return shutil.which('aria2c') is not None

    def _check_ytdlp_available(self) -> bool:
        """Check if yt-dlp is installed."""
        return shutil.which('yt-dlp') is not None

    def _build_ytdlp_command(
        self,
        m3u8_url: str,
        output_path: str,
    ) -> list[str]:
        """Build yt-dlp command with all optimizations."""
        cmd = [
            'yt-dlp',
            '--no-check-certificate',
            '-o', output_path,
            '-f',
            'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4',
            '--concurrent-fragments', '16',
        ]

        if self.use_aria2c:
            cmd.extend([
                '--downloader', 'aria2c',
                '--downloader-args',
                'aria2c:--min-split-size=1M '
                '--max-connection-per-server=16 '
                '--max-concurrent-downloads=16 '
                '--split=16',
            ])

        cmd.append(m3u8_url)

        return cmd

    def create_output_directory(self, anime: Anime, base_dir: str) -> Path:
        """Create and return output directory for anime."""
        if anime.year:
            dir_name = f"{anime.title_en} ({anime.year})"
        else:
            dir_name = anime.title_en

        output_path = Path(base_dir) / dir_name
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created output directory: {output_path}")

        return output_path

    def generate_episode_filename(
        self,
        anime: Anime,
        episode: Episode
    ) -> str:
        """Generate filename for episode."""
        base_name = (
            f"{anime.title_en} ({anime.year})"
            if anime.year
            else anime.title_en
        )

        # Format episode number with leading zero
        episode_str = f"E{episode.number:02d}"

        # Assume season 1 for now
        filename = f"{base_name} S01{episode_str}.mp4"

        return filename

    def download_episode(
        self,
        anime: Anime,
        episode: Episode,
        output_dir: Path
    ) -> bool:
        """Download a single episode."""
        if not episode.m3u8_url:
            logger.error(
                f"Episode {episode.number} has no m3u8 URL, skipping"
            )
            return False

        if not self._check_ytdlp_available():
            logger.error(
                "yt-dlp not found. Install it with: "
                "pip install yt-dlp or brew install yt-dlp"
            )
            return False

        filename = self.generate_episode_filename(anime, episode)
        output_path = output_dir / filename

        # Check if already downloaded
        if output_path.exists():
            logger.info(
                f"Episode {episode.number} already exists, skipping: "
                f"{filename}"
            )
            return True

        logger.info(
            f"Downloading episode {episode.number}/{anime.total_episodes}: "
            f"{filename}"
        )

        try:
            cmd = self._build_ytdlp_command(
                episode.m3u8_url,
                str(output_path)
            )

            # Run yt-dlp
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                logger.error(
                    f"Failed to download episode {episode.number}: "
                    f"{result.stderr}"
                )
                return False

            logger.info(
                f"Successfully downloaded episode {episode.number}: "
                f"{filename}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error downloading episode {episode.number}: {e}"
            )
            return False

    def download_all_episodes(
        self,
        anime: Anime,
        output_dir: Path,
    ) -> dict[str, int]:
        """Download all episodes and return statistics."""
        stats = {
            'total': len(anime.episodes),
            'success': 0,
            'failed': 0,
            'skipped': 0,
        }

        for episode in anime.episodes:
            result = self.download_episode(anime, episode, output_dir)

            if result:
                stats['success'] += 1
            else:
                stats['failed'] += 1

        return stats
