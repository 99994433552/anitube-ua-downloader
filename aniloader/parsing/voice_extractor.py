"""Voice and player extraction logic."""

import logging
from ..models import Voice, Player

logger = logging.getLogger(__name__)


class VoiceExtractor:
    """Extractor for voice options from playlist items."""

    # Category keywords to skip (these are usually parent containers)
    CATEGORY_KEYWORDS = [
        "ОЗВУЧЕННЯ",
        "СУБТИТРИ",
        "DUBBING",
        "SUBTITLES",
        "УКРАЇНСЬКОЮ",
        "RUSSIAN",
        "ENGLISH",
    ]

    def extract_voices(
        self,
        all_items: list[dict[str, str | int]],
        is_movie: bool,
        max_depth: int,
    ) -> list[Voice]:
        """Extract voice options from playlist items.

        Args:
            all_items: All voice/player items from playlist
            is_movie: Whether content is a movie
            max_depth: Maximum depth of items

        Returns:
            List of Voice objects
        """
        voices = []

        if is_movie:
            voices = self._extract_voices_for_movie(all_items, max_depth)
        else:
            voices = self._extract_voices_for_series(all_items, max_depth)

        logger.debug(f"Extracted {len(voices)} voices")
        return voices

    def _extract_voices_for_movie(
        self,
        all_items: list[dict[str, str | int]],
        max_depth: int,
    ) -> list[Voice]:
        """Extract voices for movie content."""
        voices = []

        # Check structure:
        # - If all items have "ПЛЕЄР" in name → use all items as players (simple structure)
        # - Otherwise → find voices (items without "ПЛЕЄР" at lower depth)
        all_have_player_keyword = all(
            "ПЛЕЄР" in str(item["name"]).upper()
            or "PLAYER" in str(item["name"]).upper()
            for item in all_items
        )

        if all_have_player_keyword:
            # Simple structure: players at top level (0_0, 0_1)
            for item in all_items:
                voices.append(Voice(id=str(item["id"]), name=str(item["name"])))
        else:
            # Complex structure: voices -> players (0_0 -> 0_0_0)
            # Only include items that are NOT players (no ПЛЕЄР keyword)
            for item in all_items:
                is_player = (
                    "ПЛЕЄР" in str(item["name"]).upper()
                    or "PLAYER" in str(item["name"]).upper()
                )
                if not is_player and item["parts_count"] < max_depth:
                    voices.append(Voice(id=str(item["id"]), name=str(item["name"])))

        return voices

    def _extract_voices_for_series(
        self,
        all_items: list[dict[str, str | int]],
        max_depth: int,
    ) -> list[Voice]:
        """Extract voices for series content."""
        voices = []

        # For series: Voices are items that:
        # 1. Are NOT at max depth (those are players)
        # 2. Don't have "ПЛЕЄР" in name (those are players)
        # 3. Are not category containers
        # Special case: If ALL items are players, then players ARE voices (simple structure)
        all_have_player_keyword = all(
            "ПЛЕЄР" in str(item["name"]).upper()
            or "PLAYER" in str(item["name"]).upper()
            for item in all_items
        )

        if all_have_player_keyword:
            # Simple structure: all items are players = voices for series
            for item in all_items:
                voices.append(Voice(id=str(item["id"]), name=str(item["name"])))
        else:
            # Complex structure: find voices (items without "ПЛЕЄР")
            for item in all_items:
                is_player = (
                    "ПЛЕЄР" in str(item["name"]).upper()
                    or "PLAYER" in str(item["name"]).upper()
                )
                is_max_depth = item["parts_count"] == max_depth
                is_category = any(
                    keyword in str(item["name"]).upper()
                    for keyword in self.CATEGORY_KEYWORDS
                )

                # Skip players, max depth items, and categories
                if is_player or (is_max_depth and max_depth > 2) or is_category:
                    continue

                voices.append(Voice(id=str(item["id"]), name=str(item["name"])))

        return voices

    def extract_players_for_voice(
        self,
        all_items: list[dict[str, str | int]],
        voice_id: str,
    ) -> list[Player]:
        """Extract player options for a specific voice.

        Args:
            all_items: All voice/player items
            voice_id: Voice ID to find players for

        Returns:
            List of Player objects
        """
        players = []
        voice_depth = len(voice_id.split("_"))
        player_depth = voice_depth + 1

        for item in all_items:
            item_id = str(item["id"])
            # Check if this item is a child of voice_id
            if (
                item_id.startswith(voice_id + "_")
                and item["parts_count"] == player_depth
            ):
                players.append(Player(id=item_id, name=str(item["name"])))

        logger.debug(f"Found {len(players)} players for voice {voice_id}")
        return players
