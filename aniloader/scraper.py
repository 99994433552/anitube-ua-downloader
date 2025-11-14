"""Web scraper for anitube.in.ua website."""

import re
import json
import logging
import urllib.parse
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .models import Anime, Voice, Player, Episode

logger = logging.getLogger(__name__)


class AnitubeScraper:
    """Scraper for extracting anime metadata and episode lists."""

    BASE_URL = "https://anitube.in.ua"
    AJAX_PLAYLIST_URL = f"{BASE_URL}/engine/ajax/playlists.php"

    def __init__(self):
        # Create session for maintaining cookies
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "sec-ch-ua": '"Chromium";v="142", "Not_A Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
            }
        )
        self._anime_url = None  # Store for Referer header

    def extract_news_id(self, url: str) -> str:
        """Extract news_id from anime URL."""
        match = re.search(r"/(\d+)-.*\.html", url)
        if not match:
            raise ValueError(f"Could not extract news_id from URL: {url}")
        return match.group(1)

    def get_user_hash(self, html: str) -> str:
        """Extract user_hash from HTML page."""
        # Try to find user_hash in script tags
        match = re.search(r'dle_login_hash\s*=\s*["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)

        # Fallback: look for common hash patterns
        match = re.search(r'user_hash["\']?\s*:\s*["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)

        # If not found, return empty string (some requests work without it)
        return ""

    def fetch_anime_metadata(self, url: str) -> Anime:
        """Fetch anime metadata from main page."""
        # Store URL for later use in Referer header
        self._anime_url = url

        response = self.session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        news_id = self.extract_news_id(url)

        # Extract English title from Twitter share link
        # Format: "Українська назва / English Name https://..."
        title_en = "Unknown"
        twitter_link = soup.find("a", href=re.compile(r"twitter\.com/intent/tweet"))
        if twitter_link:
            href = twitter_link.get("href", "")
            # Extract text parameter from URL
            match = re.search(r"text=([^&]+)", href)
            if match:
                decoded_text = urllib.parse.unquote(match.group(1))
                # Split by " / " and take English part
                if " / " in decoded_text:
                    parts = decoded_text.split(" / ")
                    if len(parts) >= 2:
                        # Remove URL at the end (everything after http)
                        english_part = re.sub(r"\s*https?://.*$", "", parts[1])
                        title_en = english_part.strip()

        # Fallback to og:title if English name not found
        if title_en == "Unknown":
            title_tag = (
                soup.find("meta", property="og:title")
                or soup.find("h1", class_="title")
                or soup.find("h1")
            )
            title_en = (
                (
                    title_tag.get("content", "")
                    if title_tag.name == "meta"
                    else title_tag.get_text(strip=True)
                )
                if title_tag
                else "Unknown"
            )

            # Clean title (remove Ukrainian additions)
            title_en = re.sub(
                r"\s*(українською|онлайн|аніме).*$", "", title_en, flags=re.IGNORECASE
            )
            title_en = title_en.strip()

        # Extract season number from English title
        # Patterns: "Name 2", "Name Season 3", "Name S2"
        season = 1  # Default to season 1
        season_patterns = [
            r"\s+(?:Season\s+)?(\d+)\s*$",  # "One Punch Man 3" or "Name Season 2"
            r"\s+S(\d+)\s*$",  # "Name S2"
        ]

        for pattern in season_patterns:
            season_match = re.search(pattern, title_en, re.IGNORECASE)
            if season_match:
                season = int(season_match.group(1))
                # Remove season number from title to get base name
                title_en = re.sub(pattern, "", title_en, flags=re.IGNORECASE).strip()
                break

        # Extract year from news_keywords meta tag or page content
        year = None
        keywords_meta = soup.find("meta", attrs={"name": "news_keywords"})
        if keywords_meta:
            keywords_content = keywords_meta.get("content", "")
            year_match = re.search(r"\b(19|20)\d{2}\b", keywords_content)
            if year_match:
                year = int(year_match.group(0))

        # Fallback: search for year in parentheses
        if not year:
            year_match = re.search(r"\((\d{4})\)", response.text)
            year = int(year_match.group(1)) if year_match else None

        # Get user hash for AJAX requests
        user_hash = self.get_user_hash(response.text)

        anime = Anime(
            news_id=news_id,
            title_en=title_en,
            year=year,
            season=season,
        )

        # Store user_hash for later use
        self._user_hash = user_hash

        return anime

    def _parse_embedded_iframe(self, anime: Anime) -> Anime:
        """Parse iframe directly from page (fallback for old format)."""
        # Fetch the original page HTML
        response = self.session.get(self._anime_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Find iframe with video player
        iframe = soup.find("iframe", src=re.compile(r"(ashdi|tortuga|monster)"))

        if not iframe:
            logger.error("No embedded iframe found on page")
            anime.is_movie = True  # Assume movie for old format
            anime.voices = []
            anime.episodes = []
            return anime

        iframe_url = iframe.get("src", "")
        if not iframe_url.startswith("http"):
            iframe_url = "https:" + iframe_url

        # For old format: single iframe = single voice/player = movie
        anime.is_movie = True
        anime.voices = [Voice(id="0", name="Єдина озвучка")]

        # Create single episode (movie)
        anime.episodes = [
            Episode(
                number=1,
                data_id="0",
                data_file=iframe_url,
            )
        ]
        anime.total_episodes = 1

        logger.info(f"Parsed embedded iframe: {iframe_url}")

        return anime

    def get_available_players(self, anime: Anime, voice_id: str) -> list[Player]:
        """Get available players for a specific voice."""
        # Need to fetch playlist first if not already done
        if not hasattr(self, "_playlist_html"):
            return []

        soup = BeautifulSoup(self._playlist_html, "lxml")

        # Find all players for this voice
        players = []
        voice_items = soup.select(".playlists-lists .playlists-items li")

        voice_depth = len(voice_id.split("_"))

        for item in voice_items:
            player_data_id = item.get("data-id", "")
            player_name = item.get_text(strip=True)

            if not player_data_id or not player_name:
                continue

            # Players are one level deeper than voice
            # and must start with voice_id
            parts = player_data_id.split("_")
            if len(parts) == voice_depth + 1 and player_data_id.startswith(voice_id):
                players.append(Player(id=player_data_id, name=player_name))

        return players

    def fetch_playlist(
        self,
        anime: Anime,
        voice_id: Optional[str] = None,
        player_id: Optional[str] = None,
    ) -> Anime:
        """Fetch playlist with episodes via AJAX."""
        params = {
            "news_id": anime.news_id,
            "xfield": "playlist",
            "user_hash": self._user_hash,
        }

        # AJAX-specific headers (override defaults for this request)
        ajax_headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self._anime_url,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }

        response = self.session.get(
            self.AJAX_PLAYLIST_URL, params=params, headers=ajax_headers
        )
        response.raise_for_status()

        # Parse JSON response
        try:
            data = response.json()
            html_content = data.get("response", "")

            # Check if AJAX returned error (old format pages)
            if not data.get("success", True) or not html_content:
                # Fallback: parse iframe directly from main page
                logger.info(
                    "AJAX playlist not available, using embedded iframe fallback"
                )
                return self._parse_embedded_iframe(anime)

        except json.JSONDecodeError:
            # Sometimes response is plain HTML
            html_content = response.text

        # Store HTML for later use (get_available_players)
        self._playlist_html = html_content

        soup = BeautifulSoup(html_content, "lxml")

        # Extract available voices
        # Flexible logic: voices are items that don't contain "ПЛЕЄР" in name
        # and are not at the deepest level (players)
        voices = []
        voice_items = soup.select(".playlists-lists .playlists-items li")

        # Collect all items first to analyze structure
        all_items = []
        for item in voice_items:
            voice_data_id = item.get("data-id", "")
            voice_name = item.get_text(strip=True)

            if not voice_data_id or not voice_name:
                continue

            parts = voice_data_id.split("_")
            all_items.append(
                {"id": voice_data_id, "name": voice_name, "parts_count": len(parts)}
            )

        # Find max depth to determine what are voices vs players
        max_depth = max((item["parts_count"] for item in all_items), default=0)

        # Detect if this is a movie vs series
        episode_items = soup.select(".playlists-videos .playlists-items li")
        episode_texts = [item.get_text(strip=True) for item in episode_items]
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
        # Multiple unique video files = series
        unique_files = set()
        for item in episode_items:
            data_file = item.get("data-file", "")
            if data_file:
                unique_files.add(data_file)

        has_multiple_episodes = len(unique_files) > len(
            all_items
        )  # More episodes than players

        # Decision logic:
        # - If has "серія" labels → definitely series
        # - If has "ФІЛЬМ" labels and only one episode → movie
        # - If multiple unique episodes → series
        # - Otherwise → movie (default for single episode)
        is_movie = (
            has_movie_label and not has_series_label and not has_multiple_episodes
        )

        # Category keywords to skip (these are usually parent containers)
        category_keywords = [
            "ОЗВУЧЕННЯ",
            "СУБТИТРИ",
            "DUBBING",
            "SUBTITLES",
            "УКРАЇНСЬКОЮ",
            "RUSSIAN",
            "ENGLISH",
        ]

        if is_movie:
            # For movies, check structure:
            # - If all items have "ПЛЕЄР" in name → use all items as players (simple structure)
            # - Otherwise → find voices (items without "ПЛЕЄР" at lower depth)
            all_have_player_keyword = all(
                "ПЛЕЄР" in item["name"].upper() or "PLAYER" in item["name"].upper()
                for item in all_items
            )

            if all_have_player_keyword:
                # Simple structure: players at top level (0_0, 0_1)
                for item in all_items:
                    voices.append(Voice(id=item["id"], name=item["name"]))
            else:
                # Complex structure: voices -> players (0_0 -> 0_0_0)
                # Only include items that are NOT players (no ПЛЕЄР keyword)
                for item in all_items:
                    is_player = (
                        "ПЛЕЄР" in item["name"].upper()
                        or "PLAYER" in item["name"].upper()
                    )
                    if not is_player and item["parts_count"] < max_depth:
                        voices.append(Voice(id=item["id"], name=item["name"]))
        else:
            # For series: Voices are items that:
            # 1. Are NOT at max depth (those are players)
            # 2. Don't have "ПЛЕЄР" in name (those are players)
            # 3. Are not category containers
            # Special case: If ALL items are players, then players ARE voices (simple structure)
            all_have_player_keyword = all(
                "ПЛЕЄР" in item["name"].upper() or "PLAYER" in item["name"].upper()
                for item in all_items
            )

            if all_have_player_keyword:
                # Simple structure: all items are players = voices for series
                for item in all_items:
                    voices.append(Voice(id=item["id"], name=item["name"]))
            else:
                # Complex structure: find voices (items without "ПЛЕЄР")
                for item in all_items:
                    is_player = (
                        "ПЛЕЄР" in item["name"].upper()
                        or "PLAYER" in item["name"].upper()
                    )
                    is_max_depth = item["parts_count"] == max_depth
                    is_category = any(
                        keyword in item["name"].upper() for keyword in category_keywords
                    )

                    # Skip players, max depth items, and categories
                    if is_player or (is_max_depth and max_depth > 2) or is_category:
                        continue

                    voices.append(Voice(id=item["id"], name=item["name"]))

        anime.voices = voices
        anime.is_movie = is_movie

        # If voice_id not specified, we'll need to select one later
        if not voice_id and voices:
            # For now, just extract episodes for first voice
            # CLI will handle voice selection
            voice_id = voices[0].id

        # Extract episodes for selected voice and player
        episodes = []
        episode_items = soup.select(".playlists-videos .playlists-items li")

        if is_movie:
            # For movies, we need to find episodes under the selected voice
            # Two cases:
            # 1. Simple: voice_id IS the player (0_0 -> episode 0_0)
            # 2. Complex: voice_id has players under it (0_0 -> players 0_0_0, 0_0_1)

            # Check if voice IS the player (simple structure)
            all_have_player_keyword = all(
                "ПЛЕЄР" in item["name"].upper() or "PLAYER" in item["name"].upper()
                for item in all_items
            )

            if all_have_player_keyword:
                # Simple case: voice IS player
                for item in episode_items:
                    data_id = item.get("data-id", "")
                    data_file = item.get("data-file", "")

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
                # Get all players for this voice
                for item in episode_items:
                    data_id = item.get("data-id", "")
                    data_file = item.get("data-file", "")

                    if not data_file:
                        continue

                    # Match episodes starting with voice_id
                    if voice_id and not data_id.startswith(voice_id):
                        continue

                    # For initial fetch without player_id, get all episodes under voice
                    # CLI will handle player selection
                    if player_id and not data_id.startswith(player_id):
                        continue

                    episodes.append(
                        Episode(
                            number=1,
                            data_id=data_id,
                            data_file=data_file,
                        )
                    )
        else:
            # Series logic: find player for voice, then extract episodes
            # Two cases:
            # 1. Simple: voice_id matches episode data_id (voice IS the player)
            # 2. Complex: voice has players under it (need to find player_id)

            # Check if any episode has voice_id as exact match (simple case)
            has_direct_episodes = any(
                item.get("data-id", "") == voice_id for item in episode_items
            )

            if has_direct_episodes:
                # Simple case: voice IS the player, episodes match voice_id directly
                # Use voice_id as player_id
                if not player_id:
                    player_id = voice_id
            elif not player_id and voice_id:
                # Complex case: find first available player under voice
                voice_depth = len(voice_id.split("_"))
                player_depth = voice_depth + 1

                for item in episode_items:
                    data_id = item.get("data-id", "")
                    if data_id.startswith(voice_id):
                        parts = data_id.split("_")
                        if len(parts) >= player_depth:
                            player_id = "_".join(parts[:player_depth])
                            break

            # Extract episodes only for the selected player
            for item in episode_items:
                data_id = item.get("data-id", "")
                data_file = item.get("data-file", "")

                if not data_file:
                    continue

                # Check if episode belongs to selected player
                if player_id:
                    if not data_id.startswith(player_id):
                        continue

                episode_num_text = item.get_text(strip=True)
                episode_num_match = re.search(r"(\d+)", episode_num_text)
                episode_num = (
                    int(episode_num_match.group(1))
                    if episode_num_match
                    else len(episodes) + 1
                )

                episodes.append(
                    Episode(
                        number=episode_num,
                        data_id=data_id,
                        data_file=data_file,
                    )
                )

        anime.episodes = episodes
        anime.total_episodes = len(episodes)

        return anime
