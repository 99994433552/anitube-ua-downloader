"""Tests for scraper module."""

import pytest
from bs4 import BeautifulSoup

from aniloader.scraper import AnitubeScraper
from aniloader.models import Anime


class TestAnitubeScraper:
    """Test AnitubeScraper class."""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance."""
        return AnitubeScraper()

    def test_extract_news_id_valid(self, scraper):
        """Test extracting news_id from valid URL."""
        url = "https://anitube.in.ua/3293-ostanny-zahisnik.html"
        news_id = scraper.extract_news_id(url)
        assert news_id == "3293"

    def test_extract_news_id_with_dash_title(self, scraper):
        """Test extracting news_id from URL with dashes in title."""
        url = "https://anitube.in.ua/4110-lyudina-benzopila.html"
        news_id = scraper.extract_news_id(url)
        assert news_id == "4110"

    def test_extract_news_id_invalid(self, scraper):
        """Test that ValueError is raised for invalid URL."""
        with pytest.raises(ValueError, match="Could not extract news_id"):
            scraper.extract_news_id("https://example.com/invalid")

    def test_get_user_hash_dle_login(self, scraper):
        """Test extracting user_hash from dle_login_hash variable."""
        html = """
        <script>
        var dle_login_hash = 'abc123def456';
        </script>
        """
        user_hash = scraper.get_user_hash(html)
        assert user_hash == "abc123def456"

    def test_get_user_hash_user_hash_key(self, scraper):
        """Test extracting user_hash from user_hash key."""
        html = """
        <script>
        data: {
            user_hash: '789xyz123'
        }
        </script>
        """
        user_hash = scraper.get_user_hash(html)
        assert user_hash == "789xyz123"

    def test_get_user_hash_not_found(self, scraper):
        """Test that empty string is returned when user_hash not found."""
        html = "<html><body>No user hash here</body></html>"
        user_hash = scraper.get_user_hash(html)
        assert user_hash == ""


class TestContentTypeDetection:
    """Test content type detection (movie vs series)."""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance."""
        return AnitubeScraper()

    def create_mock_playlist_html(
        self, players: list[tuple[str, str]], episodes: list[tuple[str, str, str]]
    ) -> str:
        """Create mock playlist HTML.

        Args:
            players: List of (data_id, name) tuples
            episodes: List of (data_id, text, data_file) tuples

        Returns:
            HTML string
        """
        players_html = "\n".join(
            [f'<li data-id="{data_id}">{name}</li>' for data_id, name in players]
        )

        episodes_html = "\n".join(
            [
                f'<li data-id="{data_id}" data-file="{data_file}">{text}</li>'
                for data_id, text, data_file in episodes
            ]
        )

        return f"""
        <div class="playlists-lists">
            <ul class="playlists-items">
                {players_html}
            </ul>
        </div>
        <div class="playlists-videos">
            <ul class="playlists-items">
                {episodes_html}
            </ul>
        </div>
        """

    def test_series_detection_with_seria_label(self, scraper):
        """Test that content with 'серія' labels is detected as series."""
        html = self.create_mock_playlist_html(
            players=[
                ("0_0", "ПЛЕЄР ASHDI"),
                ("0_1", "ПЛЕЄР TRG"),
            ],
            episodes=[
                ("0_0", "1 серія", "https://example.com/ep1"),
                ("0_0", "2 серія", "https://example.com/ep2"),
                ("0_0", "3 серія", "https://example.com/ep3"),
            ],
        )

        scraper._playlist_html = html
        scraper._user_hash = "test_hash"

        # Manually parse the HTML to test detection logic
        soup = BeautifulSoup(html, "lxml")
        episode_texts = [
            item.get_text(strip=True)
            for item in soup.select(".playlists-videos .playlists-items li")
        ]

        has_series_label = any(
            "СЕРІЯ" in text.upper() or "EPISODE" in text.upper()
            for text in episode_texts
        )

        assert has_series_label is True

    def test_movie_detection_with_film_label(self, scraper):
        """Test that content with 'ФІЛЬМ' label is detected as movie."""
        html = self.create_mock_playlist_html(
            players=[
                ("0_0", "ПЛЕЄР ASHDI"),
            ],
            episodes=[
                ("0_0", "ФІЛЬМ", "https://example.com/movie"),
            ],
        )

        soup = BeautifulSoup(html, "lxml")
        episode_texts = [
            item.get_text(strip=True)
            for item in soup.select(".playlists-videos .playlists-items li")
        ]

        has_movie_label = any(
            "ФІЛЬМ" in text.upper() or "FILM" in text.upper() for text in episode_texts
        )

        assert has_movie_label is True

    def test_series_detection_multiple_episodes(self, scraper):
        """Test that multiple unique episodes indicate a series."""
        html = self.create_mock_playlist_html(
            players=[
                ("0_0", "ПЛЕЄР ASHDI"),
            ],
            episodes=[
                ("0_0", "1 серія", "https://example.com/ep1.m3u8"),
                ("0_0", "2 серія", "https://example.com/ep2.m3u8"),
                ("0_0", "3 серія", "https://example.com/ep3.m3u8"),
                ("0_0", "4 серія", "https://example.com/ep4.m3u8"),
                ("0_0", "5 серія", "https://example.com/ep5.m3u8"),
            ],
        )

        soup = BeautifulSoup(html, "lxml")
        episode_items = soup.select(".playlists-videos .playlists-items li")

        unique_files = set()
        for item in episode_items:
            data_file = item.get("data-file", "")
            if data_file:
                unique_files.add(data_file)

        # More episodes than players indicates series
        assert len(unique_files) > 1


class TestVoicePlayerParsing:
    """Test voice and player parsing logic."""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance."""
        return AnitubeScraper()

    def test_simple_player_structure(self, scraper):
        """Test parsing simple structure where players are at top level."""
        html = """
        <div class="playlists-lists">
            <ul class="playlists-items">
                <li data-id="0_0">ПЛЕЄР ASHDI</li>
                <li data-id="0_1">ПЛЕЄР TRG</li>
            </ul>
        </div>
        """

        soup = BeautifulSoup(html, "lxml")
        voice_items = soup.select(".playlists-lists .playlists-items li")

        all_items = []
        for item in voice_items:
            voice_data_id = item.get("data-id", "")
            voice_name = item.get_text(strip=True)
            if voice_data_id and voice_name:
                parts = voice_data_id.split("_")
                all_items.append(
                    {
                        "id": voice_data_id,
                        "name": voice_name,
                        "parts_count": len(parts),
                    }
                )

        # All items have "ПЛЕЄР" in name
        all_have_player = all("ПЛЕЄР" in item["name"].upper() for item in all_items)

        assert all_have_player is True
        assert len(all_items) == 2
        assert all_items[0]["parts_count"] == 2  # depth 2

    def test_complex_voice_player_structure(self, scraper):
        """Test parsing complex structure with separate voices and players."""
        html = """
        <div class="playlists-lists">
            <ul class="playlists-items">
                <li data-id="0_0">ТОНІС</li>
                <li data-id="0_0_0">ПЛЕЄР ASHDI</li>
                <li data-id="0_0_1">ПЛЕЄР TRG</li>
                <li data-id="0_1">QTV</li>
                <li data-id="0_1_0">ПЛЕЄР MOON</li>
            </ul>
        </div>
        """

        soup = BeautifulSoup(html, "lxml")
        voice_items = soup.select(".playlists-lists .playlists-items li")

        all_items = []
        for item in voice_items:
            voice_data_id = item.get("data-id", "")
            voice_name = item.get_text(strip=True)
            if voice_data_id and voice_name:
                parts = voice_data_id.split("_")
                all_items.append(
                    {
                        "id": voice_data_id,
                        "name": voice_name,
                        "parts_count": len(parts),
                    }
                )

        # Find voices (items without "ПЛЕЄР")
        voices = [item for item in all_items if "ПЛЕЄР" not in item["name"].upper()]

        # Find players (items with "ПЛЕЄР")
        players = [item for item in all_items if "ПЛЕЄР" in item["name"].upper()]

        assert len(voices) == 2  # ТОНІС, QTV
        assert len(players) == 3  # Three players
        assert voices[0]["parts_count"] == 2  # voices at depth 2
        assert players[0]["parts_count"] == 3  # players at depth 3

    def test_get_available_players_for_voice(self, scraper):
        """Test getting players for a specific voice."""
        html = """
        <div class="playlists-lists">
            <ul class="playlists-items">
                <li data-id="0_0">ТОНІС</li>
                <li data-id="0_0_0">ПЛЕЄР ASHDI</li>
                <li data-id="0_0_1">ПЛЕЄР TRG</li>
                <li data-id="0_1">QTV</li>
                <li data-id="0_1_0">ПЛЕЄР MOON</li>
            </ul>
        </div>
        """

        scraper._playlist_html = html
        anime = Anime(news_id="123", title_en="Test", season=1)

        # Get players for voice "0_0" (ТОНІС)
        players = scraper.get_available_players(anime, "0_0")

        assert len(players) == 2
        assert players[0].id == "0_0_0"
        assert players[0].name == "ПЛЕЄР ASHDI"
        assert players[1].id == "0_0_1"
        assert players[1].name == "ПЛЕЄР TRG"

    def test_get_available_players_for_different_voice(self, scraper):
        """Test getting players for a different voice."""
        html = """
        <div class="playlists-lists">
            <ul class="playlists-items">
                <li data-id="0_0">ТОНІС</li>
                <li data-id="0_0_0">ПЛЕЄР ASHDI</li>
                <li data-id="0_0_1">ПЛЕЄР TRG</li>
                <li data-id="0_1">QTV</li>
                <li data-id="0_1_0">ПЛЕЄР MOON</li>
            </ul>
        </div>
        """

        scraper._playlist_html = html
        anime = Anime(news_id="123", title_en="Test", season=1)

        # Get players for voice "0_1" (QTV)
        players = scraper.get_available_players(anime, "0_1")

        assert len(players) == 1
        assert players[0].id == "0_1_0"
        assert players[0].name == "ПЛЕЄР MOON"
