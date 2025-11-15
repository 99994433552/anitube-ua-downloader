"""HTML parsing operations for anitube.in.ua."""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HTMLParser:
    """Parser for HTML content from anitube.in.ua."""

    def parse_soup(self, html: str) -> BeautifulSoup:
        """Parse HTML string to BeautifulSoup object.

        Args:
            html: HTML string to parse

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, "lxml")

    def parse_voice_items(self, html: str) -> list[dict[str, str | int]]:
        """Parse voice/player items from playlist HTML.

        Args:
            html: Playlist HTML content

        Returns:
            List of items with id, name, and parts_count
        """
        soup = self.parse_soup(html)
        voice_items = soup.select(".playlists-lists .playlists-items li")

        all_items = []
        for item in voice_items:
            data_id = item.get("data-id", "")
            name = item.get_text(strip=True)

            if not data_id or not name:
                continue

            parts = data_id.split("_")
            all_items.append(
                {
                    "id": data_id,
                    "name": name,
                    "parts_count": len(parts),
                }
            )

        return all_items

    def parse_episode_items(
        self, html: str, player_id: str
    ) -> list[dict[str, str | int]]:
        """Parse episode items for a specific player.

        Args:
            html: Playlist HTML content
            player_id: Player ID to filter episodes

        Returns:
            List of episode dictionaries with number, id, and file URL
        """
        soup = self.parse_soup(html)
        episode_items = soup.select(".playlists-videos .playlists-items li")

        episodes = []
        episode_number = 1

        for item in episode_items:
            data_id = item.get("data-id", "")
            data_file = item.get("data-file", "")

            if not data_id or not data_file:
                continue

            # Filter by player_id
            if not data_id.startswith(player_id):
                continue

            episodes.append(
                {
                    "number": episode_number,
                    "data_id": data_id,
                    "data_file": data_file,
                }
            )
            episode_number += 1

        return episodes

    def get_episode_texts(self, html: str) -> list[str]:
        """Extract all episode text labels from HTML.

        Args:
            html: Playlist HTML content

        Returns:
            List of episode text labels
        """
        soup = self.parse_soup(html)
        episode_items = soup.select(".playlists-videos .playlists-items li")
        return [item.get_text(strip=True) for item in episode_items]

    def get_unique_episode_files(self, html: str) -> set[str]:
        """Extract unique episode data-file URLs.

        Args:
            html: Playlist HTML content

        Returns:
            Set of unique data-file URLs
        """
        soup = self.parse_soup(html)
        episode_items = soup.select(".playlists-videos .playlists-items li")

        unique_files = set()
        for item in episode_items:
            data_file = item.get("data-file", "")
            if data_file:
                unique_files.add(data_file)

        return unique_files

    def get_max_depth(self, items: list[dict[str, str | int]]) -> int:
        """Get maximum depth from list of items.

        Args:
            items: List of items with parts_count field

        Returns:
            Maximum depth value
        """
        return max((item["parts_count"] for item in items), default=0)

    def filter_items_by_parent(
        self, items: list[dict[str, str | int]], parent_id: str
    ) -> list[dict[str, str | int]]:
        """Filter items that are children of parent_id.

        Args:
            items: List of all items
            parent_id: Parent ID to filter by (e.g., "0_0")

        Returns:
            List of child items
        """
        parent_parts = parent_id.split("_")
        parent_depth = len(parent_parts)
        target_depth = parent_depth + 1

        filtered = []
        for item in items:
            item_id = str(item["id"])
            if (
                item_id.startswith(parent_id + "_")
                and item["parts_count"] == target_depth
            ):
                filtered.append(item)

        return filtered

    def find_embedded_iframe(self, html: str) -> Optional[str]:
        """Find embedded video player iframe URL in HTML.

        Args:
            html: Page HTML content

        Returns:
            Iframe URL if found, None otherwise
        """
        soup = self.parse_soup(html)

        # Find iframe with video player
        iframe = soup.find("iframe", src=re.compile(r"(ashdi|tortuga|monster)"))

        if not iframe:
            logger.debug("No embedded iframe found in HTML")
            return None

        iframe_url = iframe.get("src", "")
        if not iframe_url:
            logger.debug("Iframe found but has no src attribute")
            return None

        # Normalize URL (add protocol if missing)
        if not iframe_url.startswith("http"):
            iframe_url = "https:" + iframe_url

        logger.debug(f"Found embedded iframe: {iframe_url}")
        return iframe_url
