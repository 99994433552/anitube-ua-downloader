"""Filesystem operations for downloads."""

import re
import logging
from pathlib import Path

from ..models import Anime, Episode

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


class FileSystemManager:
    """Manager for filesystem operations."""

    def create_output_directory(self, anime: Anime, base_dir: str) -> Path:
        """Create and return output directory for anime or movie.

        Args:
            anime: Anime object
            base_dir: Base directory path

        Returns:
            Created directory path
        """
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

    def file_exists(self, path: Path) -> bool:
        """Check if file exists.

        Args:
            path: File path

        Returns:
            True if file exists
        """
        return path.exists() and path.is_file()

    def generate_episode_filename(self, anime: Anime, episode: Episode) -> str:
        """Generate filename for episode or movie.

        Follows Jellyfin naming conventions:
        - Series: "Series Name S01E02.mp4"
        - Movies: "Movie Name (Year).mp4"

        Args:
            anime: Anime object
            episode: Episode object

        Returns:
            Generated filename
        """
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
