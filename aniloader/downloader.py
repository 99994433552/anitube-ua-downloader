"""Video downloader using yt-dlp with aria2c acceleration."""

import os
import re
import subprocess
import logging
import shutil
from pathlib import Path

from .models import Anime, Episode

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Remove or replace invalid characters in filenames.

    Args:
        filename: Original filename or directory name

    Returns:
        Sanitized filename safe for all filesystems
    """
    # Replace problematic characters
    replacements = {
        ":": " -",  # Colon → space + dash (common in subtitles like "Book 1: Water")
        "/": "-",  # Forward slash
        "\\": "-",  # Backslash
        "|": "-",  # Pipe
        "?": "",  # Question mark
        "*": "",  # Asterisk
        "<": "",  # Less than
        ">": "",  # Greater than
        '"': "'",  # Double quote → single quote
    }

    result = filename
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)

    # Remove leading/trailing spaces and dots (problematic on Windows)
    result = result.strip(". ")

    # Collapse multiple spaces
    result = re.sub(r"\s+", " ", result)

    return result


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
        return shutil.which("aria2c") is not None

    def _check_ytdlp_available(self) -> bool:
        """Check if yt-dlp is installed."""
        return shutil.which("yt-dlp") is not None

    def _build_ytdlp_command(
        self,
        m3u8_url: str,
        output_path: str,
    ) -> list[str]:
        """Build yt-dlp command with all optimizations."""
        cmd = [
            "yt-dlp",
            "--no-check-certificate",
            "-o",
            output_path,
        ]

        # For direct MP4 files (not HLS), use simpler options
        if ".m3u8" in m3u8_url or "/hls/" in m3u8_url:
            # HLS stream - use format selection and merging
            cmd.extend(
                [
                    "-f",
                    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--merge-output-format",
                    "mp4",
                    "--concurrent-fragments",
                    "16",
                ]
            )
        else:
            # Direct MP4 file - force generic extractor and allow unusual extensions
            cmd.extend(
                [
                    "--force-generic-extractor",
                    "--compat-options",
                    "no-sanitize-ext",
                ]
            )

        if self.use_aria2c:
            cmd.extend(
                [
                    "--downloader",
                    "aria2c",
                    "--downloader-args",
                    "aria2c:--min-split-size=1M "
                    "--max-connection-per-server=16 "
                    "--max-concurrent-downloads=16 "
                    "--split=16",
                ]
            )

        cmd.append(m3u8_url)

        return cmd

    def create_output_directory(self, anime: Anime, base_dir: str) -> Path:
        """Create and return output directory for anime or movie."""
        if anime.is_movie:
            # Movies: Movie Name (Year)/
            if anime.year:
                folder_name = f"{anime.title_en} ({anime.year})"
            else:
                folder_name = anime.title_en

            folder_name = sanitize_filename(folder_name)
            output_path = Path(base_dir) / folder_name
        else:
            # Series: Series Name/Season XX/
            series_name = sanitize_filename(anime.title_en)
            season_folder = f"Season {anime.season:02d}"
            output_path = Path(base_dir) / series_name / season_folder

        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_path}")

        return output_path

    def generate_episode_filename(self, anime: Anime, episode: Episode) -> str:
        """Generate filename for episode or movie."""
        if anime.is_movie:
            # Movies: Movie Name (Year).mp4
            if anime.year:
                filename = f"{anime.title_en} ({anime.year}).mp4"
            else:
                filename = f"{anime.title_en}.mp4"
        else:
            # Series: Series Name S01E02.mp4
            base_name = anime.title_en
            filename = f"{base_name} S{anime.season:02d}E{episode.number:02d}.mp4"

        return sanitize_filename(filename)

    def _download_with_aria2c(self, url: str, output_path: str) -> bool:
        """Download direct file with aria2c."""
        cmd = [
            "aria2c",
            "--max-connection-per-server=16",
            "--split=16",
            "--min-split-size=1M",
            "--max-concurrent-downloads=16",
            "--allow-overwrite=true",
            "--auto-file-renaming=false",
            "--check-certificate=false",
            "--out",
            os.path.basename(output_path),
            "--dir",
            os.path.dirname(output_path),
            url,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        return result.returncode == 0

    def download_episode(
        self, anime: Anime, episode: Episode, output_dir: Path
    ) -> bool:
        """Download a single episode."""
        if not episode.m3u8_url:
            logger.error(f"Episode {episode.number} has no m3u8 URL, skipping")
            return False

        filename = self.generate_episode_filename(anime, episode)
        output_path = output_dir / filename

        # Check if already downloaded
        if output_path.exists():
            logger.info(
                f"Episode {episode.number} already exists, skipping: {filename}"
            )
            return True

        logger.info(
            f"Downloading episode {episode.number}/{anime.total_episodes}: {filename}"
        )

        try:
            # Check if this is a direct MP4 file (not HLS)
            is_direct_file = (
                ".mp4" in episode.m3u8_url and ".m3u8" not in episode.m3u8_url
            )

            if is_direct_file and self.use_aria2c:
                # Use aria2c directly for MP4 files to avoid yt-dlp extension issues
                logger.debug("Using aria2c for direct MP4 download")
                result = self._download_with_aria2c(episode.m3u8_url, str(output_path))

                if not result:
                    logger.error(
                        f"Failed to download episode {episode.number} with aria2c"
                    )
                    return False
            else:
                # Use yt-dlp for HLS streams
                if not self._check_ytdlp_available():
                    logger.error(
                        "yt-dlp not found. Install it with: "
                        "pip install yt-dlp or brew install yt-dlp"
                    )
                    return False

                cmd = self._build_ytdlp_command(episode.m3u8_url, str(output_path))

                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )

                if result.returncode != 0:
                    logger.error(
                        f"Failed to download episode {episode.number}: {result.stderr}"
                    )
                    return False

            logger.info(f"Successfully downloaded episode {episode.number}: {filename}")
            return True

        except Exception as e:
            logger.error(f"Error downloading episode {episode.number}: {e}")
            return False

    def download_all_episodes(
        self,
        anime: Anime,
        output_dir: Path,
    ) -> dict[str, int]:
        """Download all episodes and return statistics."""
        stats = {
            "total": len(anime.episodes),
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

        for episode in anime.episodes:
            result = self.download_episode(anime, episode, output_dir)

            if result:
                stats["success"] += 1
            else:
                stats["failed"] += 1

        return stats
