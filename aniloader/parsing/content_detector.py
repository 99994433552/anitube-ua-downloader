"""Content type detection (movie vs series)."""

import logging

logger = logging.getLogger(__name__)


class ContentTypeDetector:
    """Detector for content type (movie vs series)."""

    def detect_is_movie(
        self,
        episode_texts: list[str],
        unique_files_count: int,
        total_items_count: int,
    ) -> bool:
        """Determine if content is a movie or series.

        Uses multiple heuristics:
        1. Explicit labels ("ФІЛЬМ"/"FILM" vs "серія"/"episode")
        2. Number of unique episodes (multiple episodes = series)
        3. Ratio of episodes to player options

        Args:
            episode_texts: List of episode text labels
            unique_files_count: Number of unique video file URLs
            total_items_count: Total number of voice/player items

        Returns:
            True if movie, False if series
        """
        unique_episode_texts = set(episode_texts)

        # Method 1: Check if labeled as "ФІЛЬМ"/"FILM" (explicit movie marker)
        has_movie_label = any(
            "ФІЛЬМ" in text.upper() or "FILM" in text.upper()
            for text in unique_episode_texts
        )

        # Method 2: Check if labeled as "серія"/"episode" (explicit series marker)
        has_series_label = any(
            "СЕРІЯ" in text.upper()
            or "EPISODE" in text.upper()
            or "ЕПІЗОД" in text.upper()
            for text in unique_episode_texts
        )

        # Method 3: Count unique episodes (by data-file, not data-id)
        # If there are more unique video files than voice/player items,
        # it means multiple episodes exist (series). For movies, each voice/player
        # typically has exactly one video file, so unique_files_count <= total_items_count.
        has_multiple_episodes = unique_files_count > total_items_count

        # Decision logic:
        # - If has "серія" labels → definitely series
        # - If multiple unique episodes → series
        # - Otherwise → movie (default for single episode or explicit movie label)
        if has_series_label:
            is_movie = False
        elif has_multiple_episodes:
            is_movie = False
        else:
            # Single episode without series labels = movie (or explicit movie label)
            is_movie = True

        logger.debug(
            f"Content type detection: has_movie_label={has_movie_label}, "
            f"has_series_label={has_series_label}, "
            f"has_multiple_episodes={has_multiple_episodes}, "
            f"is_movie={is_movie}"
        )

        return is_movie
