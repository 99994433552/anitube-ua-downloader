"""Filename generation for Jellyfin compatibility."""

import logging

from ..models import Anime, Episode
from .filesystem import sanitize_filename

logger = logging.getLogger(__name__)


class FilenameGenerator:
    """Generator for Jellyfin-compatible filenames."""

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
