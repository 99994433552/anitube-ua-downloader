"""Episode extraction logic from playlist HTML."""

import logging
from ..models import Episode

logger = logging.getLogger(__name__)


class EpisodeExtractor:
    """Extractor for episode lists from playlist HTML."""

    def extract_episodes(
        self,
        episode_items: list[dict[str, str]],
        voice_id: str,
        player_id: str | None,
        is_movie: bool,
        all_items: list[dict[str, str | int]],
    ) -> list[Episode]:
        """Extract episodes for selected voice and player.

        Args:
            episode_items: Episode items from HTML parser
            voice_id: Selected voice ID
            player_id: Selected player ID (optional)
            is_movie: Whether content is a movie
            all_items: All voice/player items

        Returns:
            List of Episode objects
        """
        if is_movie:
            return self._extract_movie_episodes(
                episode_items, voice_id, player_id, all_items
            )
        else:
            return self._extract_series_episodes(episode_items, voice_id, player_id)

    def _extract_movie_episodes(
        self,
        episode_items: list[dict[str, str]],
        voice_id: str,
        player_id: str | None,
        all_items: list[dict[str, str | int]],
    ) -> list[Episode]:
        """Extract episodes for movie (usually just 1)."""
        episodes = []

        # For movies, we need to find episodes under the selected voice
        # Two cases:
        # 1. Simple: voice_id IS the player (0_0 -> episode 0_0)
        # 2. Complex: voice_id has players under it (0_0 -> players 0_0_0, 0_0_1)

        # Check if voice IS the player (simple structure)
        all_have_player_keyword = all(
            "ПЛЕЄР" in str(item["name"]).upper()
            or "PLAYER" in str(item["name"]).upper()
            for item in all_items
        )

        if all_have_player_keyword:
            # Simple case: voice IS player
            for item in episode_items:
                data_id = item.get("data_id", "")
                data_file = item.get("data_file", "")

                if not data_file:
                    continue

                # Match exact voice/player ID
                if voice_id and data_id != voice_id:
                    continue

                episodes.append(
                    Episode(
                        number=1,
                        data_id=data_id,
                        data_file=data_file,
                    )
                )
        else:
            # Complex case: voice has players under it
            for item in episode_items:
                data_id = item.get("data_id", "")
                data_file = item.get("data_file", "")

                if not data_file:
                    continue

                # Match episodes starting with voice_id
                if voice_id and not data_id.startswith(voice_id):
                    continue

                # For initial fetch without player_id, get all episodes under voice
                if player_id and not data_id.startswith(player_id):
                    continue

                episodes.append(
                    Episode(
                        number=1,
                        data_id=data_id,
                        data_file=data_file,
                    )
                )

        logger.debug(f"Extracted {len(episodes)} movie episodes")
        return episodes

    def _extract_series_episodes(
        self,
        episode_items: list[dict[str, str]],
        voice_id: str,
        player_id: str | None,
    ) -> list[Episode]:
        """Extract episodes for series."""
        episodes = []

        # Series logic: find player for voice, then extract episodes
        # Two cases:
        # 1. Simple: voice_id matches episode data_id (voice IS the player)
        # 2. Complex: voice has players under it (need to find player_id)

        # Check if any episode has voice_id as exact match (simple case)
        has_direct_episodes = any(
            item.get("data_id", "") == voice_id for item in episode_items
        )

        if has_direct_episodes and not player_id:
            # Simple case: voice IS the player, use voice_id as player_id
            player_id = voice_id
        elif not player_id and voice_id:
            # Complex case: find first available player under voice
            voice_depth = len(voice_id.split("_"))
            player_depth = voice_depth + 1

            for item in episode_items:
                data_id = item.get("data_id", "")
                if data_id.startswith(voice_id):
                    parts = data_id.split("_")
                    if len(parts) >= player_depth:
                        player_id = "_".join(parts[:player_depth])
                        break

        # Extract episodes only for the selected player
        for idx, item in enumerate(episode_items, 1):
            data_id = item.get("data_id", "")
            data_file = item.get("data_file", "")

            if not data_file:
                continue

            # Check if episode belongs to selected player
            if player_id and not data_id.startswith(player_id):
                continue

            # Try to extract episode number from item (if available)
            episode_num = item.get("number", idx)

            episodes.append(
                Episode(
                    number=episode_num,
                    data_id=data_id,
                    data_file=data_file,
                )
            )

        logger.debug(f"Extracted {len(episodes)} series episodes")
        return episodes
