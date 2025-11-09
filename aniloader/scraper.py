"""Web scraper for anitube.in.ua website."""

import re
import json
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .models import Anime, Voice, Player, Episode


class AnitubeScraper:
    """Scraper for extracting anime metadata and episode lists."""

    BASE_URL = "https://anitube.in.ua"
    AJAX_PLAYLIST_URL = f"{BASE_URL}/engine/ajax/playlists.php"

    def __init__(self):
        # Create session for maintaining cookies
        self.session = requests.Session()
        self.session.headers.update({
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
        })
        self._anime_url = None  # Store for Referer header

    def extract_news_id(self, url: str) -> str:
        """Extract news_id from anime URL."""
        match = re.search(r'/(\d+)-.*\.html', url)
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

        soup = BeautifulSoup(response.text, 'lxml')
        news_id = self.extract_news_id(url)

        # Extract title (English)
        # Look for title in meta tags or h1
        title_tag = (
            soup.find('meta', property='og:title') or
            soup.find('h1', class_='title') or
            soup.find('h1')
        )
        title_en = (
            title_tag.get('content', '') if title_tag.name == 'meta'
            else title_tag.get_text(strip=True)
        ) if title_tag else "Unknown"

        # Clean title (remove extra info in parentheses if needed)
        title_en = re.sub(r'\s*\([^)]*AC1B8B@[^)]*\)', '', title_en,
                         flags=re.IGNORECASE)
        title_en = title_en.strip()

        # Extract year from title or page
        year_match = re.search(r'\((\d{4})\)', response.text)
        year = int(year_match.group(1)) if year_match else None

        # Get user hash for AJAX requests
        user_hash = self.get_user_hash(response.text)

        anime = Anime(
            news_id=news_id,
            title_en=title_en,
            year=year,
        )

        # Store user_hash for later use
        self._user_hash = user_hash

        return anime

    def get_available_players(
        self,
        anime: Anime,
        voice_id: str
    ) -> list[Player]:
        """Get available players for a specific voice."""
        # Need to fetch playlist first if not already done
        if not hasattr(self, '_playlist_html'):
            return []

        soup = BeautifulSoup(self._playlist_html, 'lxml')

        # Find all players for this voice
        players = []
        voice_items = soup.select('.playlists-lists .playlists-items li')

        for item in voice_items:
            player_data_id = item.get('data-id', '')
            player_name = item.get_text(strip=True)

            if not player_data_id or not player_name:
                continue

            # Players have 4 parts: X_X_X_X
            # Must start with voice_id (3 parts)
            parts = player_data_id.split('_')
            if len(parts) == 4 and player_data_id.startswith(voice_id):
                players.append(Player(
                    id=player_data_id,
                    name=player_name
                ))

        return players

    def fetch_playlist(
        self,
        anime: Anime,
        voice_id: Optional[str] = None,
        player_id: Optional[str] = None
    ) -> Anime:
        """Fetch playlist with episodes via AJAX."""
        params = {
            'news_id': anime.news_id,
            'xfield': 'playlist',
            'user_hash': self._user_hash,
        }

        # AJAX-specific headers (override defaults for this request)
        ajax_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': self._anime_url,
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }

        response = self.session.get(
            self.AJAX_PLAYLIST_URL,
            params=params,
            headers=ajax_headers
        )
        response.raise_for_status()

        # Parse JSON response
        try:
            data = response.json()
            html_content = data.get('response', '')
        except json.JSONDecodeError:
            # Sometimes response is plain HTML
            html_content = response.text

        # Store HTML for later use (get_available_players)
        self._playlist_html = html_content

        soup = BeautifulSoup(html_content, 'lxml')

        # Extract available voices
        # Only get actual voice options (3rd level: X_X_X format)
        # Skip categories (X_X) and players (X_X_X_X)
        voices = []
        voice_items = soup.select('.playlists-lists .playlists-items li')
        for item in voice_items:
            voice_data_id = item.get('data-id', '')
            voice_name = item.get_text(strip=True)

            if not voice_data_id or not voice_name:
                continue

            # Count underscores to determine level
            # X_X = category (2 parts) - skip
            # X_X_X = voice (3 parts) - include
            # X_X_X_X = player (4 parts) - skip
            parts = voice_data_id.split('_')
            if len(parts) == 3:  # Only voices (3rd level)
                voices.append(Voice(id=voice_data_id, name=voice_name))

        anime.voices = voices

        # If voice_id not specified, we'll need to select one later
        if not voice_id and voices:
            # For now, just extract episodes for first voice
            # CLI will handle voice selection
            voice_id = voices[0].id

        # Extract episodes for selected voice and player
        episodes = []
        episode_items = soup.select('.playlists-videos .playlists-items li')

        # If player_id not specified, find first available player
        if not player_id and voice_id:
            for item in episode_items:
                data_id = item.get('data-id', '')
                if data_id.startswith(voice_id):
                    parts = data_id.split('_')
                    if len(parts) >= 4:
                        player_id = '_'.join(parts[:4])
                        break

        # Extract episodes only for the selected player
        for item in episode_items:
            data_id = item.get('data-id', '')
            data_file = item.get('data-file', '')

            if not data_file:
                continue

            # Check if episode belongs to selected player
            if player_id:
                if not data_id.startswith(player_id):
                    continue

            episode_num_text = item.get_text(strip=True)
            episode_num_match = re.search(r'(\d+)', episode_num_text)
            episode_num = (
                int(episode_num_match.group(1))
                if episode_num_match else len(episodes) + 1
            )

            episodes.append(Episode(
                number=episode_num,
                data_id=data_id,
                data_file=data_file,
            ))

        anime.episodes = episodes
        anime.total_episodes = len(episodes)

        return anime
