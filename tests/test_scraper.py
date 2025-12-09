"""Tests for scraper module."""

import pytest
from bs4 import BeautifulSoup

from aniloader.scraper_refactored import AnitubeScraper
from aniloader.parsing.content_detector import ContentTypeDetector
from aniloader.parsing.voice_extractor import VoiceExtractor
from aniloader.parsing.html_parser import HTMLParser
from aniloader.parsing.metadata_extractor import MetadataExtractor
from aniloader.parsing.episode_extractor import EpisodeExtractor


class TestAnitubeScraper:
    """Test AnitubeScraper class."""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance."""
        return AnitubeScraper()


class TestContentTypeDetector:
    """Test ContentTypeDetector class."""

    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return ContentTypeDetector()

    def test_detect_is_movie_with_film_label(self, detector):
        """Test that content with 'ФІЛЬМ' label is detected as movie."""
        episode_texts = ["ФІЛЬМ"]
        is_movie = detector.detect_is_movie(
            episode_texts=episode_texts,
            unique_files_count=1,
            total_items_count=1,
        )
        assert is_movie is True

    def test_detect_is_movie_with_series_label(self, detector):
        """Test that content with 'серія' label is detected as series."""
        episode_texts = ["1 серія", "2 серія", "3 серія"]
        is_movie = detector.detect_is_movie(
            episode_texts=episode_texts,
            unique_files_count=3,
            total_items_count=1,
        )
        assert is_movie is False

    def test_detect_is_movie_single_episode_no_label(self, detector):
        """Test that single episode without labels is detected as movie."""
        episode_texts = ["Відео"]
        is_movie = detector.detect_is_movie(
            episode_texts=episode_texts,
            unique_files_count=1,
            total_items_count=1,
        )
        assert is_movie is True

    def test_detect_is_movie_multiple_episodes(self, detector):
        """Test that multiple episodes indicate series."""
        episode_texts = ["Ep 1", "Ep 2", "Ep 3", "Ep 4", "Ep 5"]
        is_movie = detector.detect_is_movie(
            episode_texts=episode_texts,
            unique_files_count=5,
            total_items_count=2,  # Less than unique files
        )
        assert is_movie is False

    def test_detect_is_movie_with_episode_label(self, detector):
        """Test that 'EPISODE' label indicates series."""
        episode_texts = ["Episode 1", "Episode 2"]
        is_movie = detector.detect_is_movie(
            episode_texts=episode_texts,
            unique_files_count=2,
            total_items_count=1,
        )
        assert is_movie is False

    def test_detect_is_movie_with_epizod_label(self, detector):
        """Test that 'ЕПІЗОД' label indicates series."""
        episode_texts = ["ЕПІЗОД 1", "ЕПІЗОД 2"]
        is_movie = detector.detect_is_movie(
            episode_texts=episode_texts,
            unique_files_count=2,
            total_items_count=1,
        )
        assert is_movie is False


class TestVoiceExtractor:
    """Test VoiceExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return VoiceExtractor()

    def test_extract_voices_simple_structure(self, extractor):
        """Test extracting voices from simple structure (all players)."""
        all_items = [
            {"id": "0_0", "name": "ПЛЕЄР ASHDI", "parts_count": 2},
            {"id": "0_1", "name": "ПЛЕЄР TRG", "parts_count": 2},
        ]
        voices = extractor.extract_voices(all_items, is_movie=False, max_depth=2)

        assert len(voices) == 2
        assert voices[0].id == "0_0"
        assert voices[0].name == "ПЛЕЄР ASHDI"

    def test_extract_voices_complex_structure(self, extractor):
        """Test extracting voices from complex structure (voices + players)."""
        all_items = [
            {"id": "0_0", "name": "ТОНІС", "parts_count": 2},
            {"id": "0_0_0", "name": "ПЛЕЄР ASHDI", "parts_count": 3},
            {"id": "0_0_1", "name": "ПЛЕЄР TRG", "parts_count": 3},
            {"id": "0_1", "name": "QTV", "parts_count": 2},
            {"id": "0_1_0", "name": "ПЛЕЄР MOON", "parts_count": 3},
        ]
        voices = extractor.extract_voices(all_items, is_movie=False, max_depth=3)

        assert len(voices) == 2
        assert voices[0].name == "ТОНІС"
        assert voices[1].name == "QTV"

    def test_extract_players_for_voice(self, extractor):
        """Test extracting players for a specific voice."""
        all_items = [
            {"id": "0_0", "name": "ТОНІС", "parts_count": 2},
            {"id": "0_0_0", "name": "ПЛЕЄР ASHDI", "parts_count": 3},
            {"id": "0_0_1", "name": "ПЛЕЄР TRG", "parts_count": 3},
            {"id": "0_1", "name": "QTV", "parts_count": 2},
            {"id": "0_1_0", "name": "ПЛЕЄР MOON", "parts_count": 3},
        ]
        players = extractor.extract_players_for_voice(all_items, "0_0")

        assert len(players) == 2
        assert players[0].id == "0_0_0"
        assert players[0].name == "ПЛЕЄР ASHDI"
        assert players[1].id == "0_0_1"

    def test_extract_players_for_different_voice(self, extractor):
        """Test extracting players for different voice."""
        all_items = [
            {"id": "0_0", "name": "ТОНІС", "parts_count": 2},
            {"id": "0_0_0", "name": "ПЛЕЄР ASHDI", "parts_count": 3},
            {"id": "0_1", "name": "QTV", "parts_count": 2},
            {"id": "0_1_0", "name": "ПЛЕЄР MOON", "parts_count": 3},
        ]
        players = extractor.extract_players_for_voice(all_items, "0_1")

        assert len(players) == 1
        assert players[0].id == "0_1_0"
        assert players[0].name == "ПЛЕЄР MOON"

    def test_extract_voices_skips_categories(self, extractor):
        """Test that category keywords are skipped."""
        all_items = [
            {"id": "0", "name": "ОЗВУЧЕННЯ", "parts_count": 1},
            {"id": "0_0", "name": "ТОНІС", "parts_count": 2},
            {"id": "0_1", "name": "QTV", "parts_count": 2},
        ]
        voices = extractor.extract_voices(all_items, is_movie=False, max_depth=2)

        # Should skip "ОЗВУЧЕННЯ" category
        assert len(voices) == 2
        assert all("ОЗВУЧЕННЯ" not in v.name for v in voices)


class TestHTMLParser:
    """Test HTMLParser class."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return HTMLParser()

    def test_parse_soup(self, parser):
        """Test parsing HTML to BeautifulSoup."""
        html = "<html><body><h1>Test</h1></body></html>"
        soup = parser.parse_soup(html)
        assert soup.find("h1").get_text() == "Test"

    def test_parse_voice_items(self, parser, mock_playlist_html):
        """Test parsing voice items from playlist HTML."""
        html = mock_playlist_html(
            players=[("0_0", "ПЛЕЄР ASHDI"), ("0_1", "ПЛЕЄР TRG")],
            episodes=[],
        )
        items = parser.parse_voice_items(html)

        assert len(items) == 2
        assert items[0]["id"] == "0_0"
        assert items[0]["name"] == "ПЛЕЄР ASHDI"

    def test_parse_voice_items_skips_empty(self, parser):
        """Test that items without id or name are skipped."""
        html = """
        <div class="playlists-lists">
            <ul class="playlists-items">
                <li data-id="0_0">Valid</li>
                <li data-id="">Empty ID</li>
                <li>No data-id</li>
            </ul>
        </div>
        """
        items = parser.parse_voice_items(html)
        assert len(items) == 1
        assert items[0]["name"] == "Valid"

    def test_parse_episode_items(self, parser, mock_playlist_html):
        """Test parsing episode items for a player."""
        html = mock_playlist_html(
            players=[("0_0", "ПЛЕЄР ASHDI")],
            episodes=[
                ("0_0_0", "Episode 1", "https://example.com/ep1"),
                ("0_0_1", "Episode 2", "https://example.com/ep2"),
                ("0_1_0", "Other Player Ep", "https://example.com/other"),
            ],
        )
        episodes = parser.parse_episode_items(html, "0_0")

        assert len(episodes) == 2
        assert episodes[0]["data_file"] == "https://example.com/ep1"
        assert episodes[1]["data_file"] == "https://example.com/ep2"

    def test_parse_episode_items_skips_invalid(self, parser):
        """Test that episodes without id or file are skipped."""
        html = """
        <div class="playlists-videos">
            <ul class="playlists-items">
                <li data-id="0_0" data-file="https://valid.com">Valid</li>
                <li data-id="0_1" data-file="">No file</li>
                <li data-id="" data-file="https://no-id.com">No ID</li>
            </ul>
        </div>
        """
        episodes = parser.parse_episode_items(html, "0")
        assert len(episodes) == 1
        assert episodes[0]["data_file"] == "https://valid.com"

    def test_get_episode_texts(self, parser, mock_playlist_html):
        """Test extracting episode text labels."""
        html = mock_playlist_html(
            players=[("0_0", "Player")],
            episodes=[
                ("0_0", "1 серія", "https://ep1"),
                ("0_0", "2 серія", "https://ep2"),
            ],
        )
        texts = parser.get_episode_texts(html)

        assert len(texts) == 2
        assert texts[0] == "1 серія"
        assert texts[1] == "2 серія"

    def test_get_unique_episode_files(self, parser):
        """Test extracting unique data-file URLs."""
        html = """
        <div class="playlists-videos">
            <ul class="playlists-items">
                <li data-id="0_0" data-file="https://file1.com">Ep 1</li>
                <li data-id="0_1" data-file="https://file2.com">Ep 2</li>
                <li data-id="0_2" data-file="https://file1.com">Ep 3 (duplicate)</li>
                <li data-id="0_3" data-file="">No file</li>
            </ul>
        </div>
        """
        files = parser.get_unique_episode_files(html)

        assert len(files) == 2
        assert "https://file1.com" in files
        assert "https://file2.com" in files

    def test_get_max_depth(self, parser):
        """Test getting max depth from items."""
        items = [
            {"id": "0_0", "name": "Item 1", "parts_count": 2},
            {"id": "0_0_0", "name": "Item 2", "parts_count": 3},
            {"id": "0_1", "name": "Item 3", "parts_count": 2},
        ]
        assert parser.get_max_depth(items) == 3

    def test_get_max_depth_empty(self, parser):
        """Test max depth with empty list."""
        assert parser.get_max_depth([]) == 0

    def test_filter_items_by_parent(self, parser):
        """Test filtering items by parent ID."""
        items = [
            {"id": "0_0", "name": "Voice 1", "parts_count": 2},
            {"id": "0_0_0", "name": "Player 1", "parts_count": 3},
            {"id": "0_0_1", "name": "Player 2", "parts_count": 3},
            {"id": "0_1", "name": "Voice 2", "parts_count": 2},
            {"id": "0_1_0", "name": "Player 3", "parts_count": 3},
        ]
        filtered = parser.filter_items_by_parent(items, "0_0")

        assert len(filtered) == 2
        assert filtered[0]["id"] == "0_0_0"
        assert filtered[1]["id"] == "0_0_1"

    def test_find_embedded_iframe_found(self, parser):
        """Test finding embedded iframe URL."""
        html = """
        <html><body>
            <iframe src="//ashdi.vip/player/12345"></iframe>
        </body></html>
        """
        url = parser.find_embedded_iframe(html)
        assert url == "https://ashdi.vip/player/12345"

    def test_find_embedded_iframe_tortuga(self, parser):
        """Test finding tortuga iframe."""
        html = """
        <html><body>
            <iframe src="https://tortuga.wtf/video/abc123"></iframe>
        </body></html>
        """
        url = parser.find_embedded_iframe(html)
        assert url == "https://tortuga.wtf/video/abc123"

    def test_find_embedded_iframe_not_found(self, parser):
        """Test when no iframe is found."""
        html = "<html><body><p>No iframe here</p></body></html>"
        assert parser.find_embedded_iframe(html) is None

    def test_find_embedded_iframe_no_src(self, parser):
        """Test when iframe has no src attribute."""
        html = """
        <html><body>
            <iframe></iframe>
        </body></html>
        """
        # No matching iframe (regex won't match empty src)
        assert parser.find_embedded_iframe(html) is None


class TestVoicePlayerParsing:
    """Test voice and player parsing integration."""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance."""
        return AnitubeScraper()

    def test_simple_player_structure(self, mock_playlist_html):
        """Test parsing simple structure where players are at top level."""
        html = mock_playlist_html(
            players=[("0_0", "ПЛЕЄР ASHDI"), ("0_1", "ПЛЕЄР TRG")],
            episodes=[],
        )
        soup = BeautifulSoup(html, "lxml")
        voice_items = soup.select(".playlists-lists .playlists-items li")

        all_items = []
        for item in voice_items:
            voice_data_id = item.get("data-id", "")
            voice_name = item.get_text(strip=True)
            if voice_data_id and voice_name:
                parts = str(voice_data_id).split("_")
                all_items.append(
                    {
                        "id": voice_data_id,
                        "name": voice_name,
                        "parts_count": len(parts),
                    }
                )

        # All items have "ПЛЕЄР" in name
        all_have_player = all(
            "ПЛЕЄР" in str(item["name"]).upper() for item in all_items
        )

        assert all_have_player is True
        assert len(all_items) == 2
        assert all_items[0]["parts_count"] == 2

    def test_complex_voice_player_structure(self, mock_playlist_html):
        """Test parsing complex structure with separate voices and players."""
        # Need to create HTML manually since mock_playlist_html
        # puts all items in the same list
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
                parts = str(voice_data_id).split("_")
                all_items.append(
                    {
                        "id": voice_data_id,
                        "name": voice_name,
                        "parts_count": len(parts),
                    }
                )

        # Find voices (items without "ПЛЕЄР")
        voices = [
            item for item in all_items if "ПЛЕЄР" not in str(item["name"]).upper()
        ]

        # Find players (items with "ПЛЕЄР")
        players = [item for item in all_items if "ПЛЕЄР" in str(item["name"]).upper()]

        assert len(voices) == 2  # ТОНІС, QTV
        assert len(players) == 3  # Three players


class TestSeriesDetection:
    """Test series vs movie detection."""

    def test_series_detection_with_seria_label(self, mock_playlist_html):
        """Test that content with 'серія' labels is detected as series."""
        html = mock_playlist_html(
            players=[("0_0", "ПЛЕЄР ASHDI")],
            episodes=[
                ("0_0", "1 серія", "https://example.com/ep1"),
                ("0_0", "2 серія", "https://example.com/ep2"),
                ("0_0", "3 серія", "https://example.com/ep3"),
            ],
        )
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

    def test_movie_detection_with_film_label(self, mock_playlist_html):
        """Test that content with 'ФІЛЬМ' label is detected as movie."""
        html = mock_playlist_html(
            players=[("0_0", "ПЛЕЄР ASHDI")],
            episodes=[("0_0", "ФІЛЬМ", "https://example.com/movie")],
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


class TestMetadataExtractor:
    """Test MetadataExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return MetadataExtractor()

    def test_extract_news_id_valid(self, extractor):
        """Test extracting news_id from valid URL."""
        url = "https://anitube.in.ua/12345-anime-name.html"
        assert extractor.extract_news_id(url) == "12345"

    def test_extract_news_id_complex_url(self, extractor):
        """Test extracting news_id from complex URL."""
        url = "https://anitube.in.ua/67890-some-long-anime-title-here.html"
        assert extractor.extract_news_id(url) == "67890"

    def test_extract_news_id_invalid(self, extractor):
        """Test that invalid URL raises ValueError."""
        url = "https://anitube.in.ua/invalid-url"
        with pytest.raises(ValueError, match="Could not extract news_id"):
            extractor.extract_news_id(url)

    def test_extract_user_hash_dle_login(self, extractor):
        """Test extracting user hash from dle_login_hash."""
        html = """
        <script>
            var dle_login_hash = "abc123def456";
        </script>
        """
        assert extractor.extract_user_hash(html) == "abc123def456"

    def test_extract_user_hash_user_hash(self, extractor):
        """Test extracting user hash from user_hash pattern."""
        html = """
        <script>
            user_hash: "xyz789"
        </script>
        """
        assert extractor.extract_user_hash(html) == "xyz789"

    def test_extract_user_hash_not_found(self, extractor):
        """Test that missing hash returns empty string."""
        html = "<html><body>No hash here</body></html>"
        assert extractor.extract_user_hash(html) == ""

    def test_extract_title_from_twitter(self, extractor):
        """Test extracting English title from Twitter share link."""
        html = """
        <html><body>
            <a href="https://twitter.com/intent/tweet?text=Українська%20Назва%20/%20English%20Title%20https://example.com">Share</a>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        title = extractor.extract_title(soup)
        assert title == "English Title"

    def test_extract_title_from_og_tag(self, extractor):
        """Test extracting title from og:title meta tag."""
        html = """
        <html>
        <head>
            <meta property="og:title" content="Anime Title from OG">
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        title = extractor.extract_title(soup)
        assert title == "Anime Title from OG"

    def test_extract_title_from_h1(self, extractor):
        """Test extracting title from h1 tag with title class."""
        html = """
        <html><body>
            <h1 class="title">Title from H1</h1>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        title = extractor.extract_title(soup)
        assert title == "Title from H1"

    def test_extract_title_unknown(self, extractor):
        """Test default title when none found."""
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, "lxml")
        title = extractor.extract_title(soup)
        assert title == "Unknown"

    def test_extract_season_with_season_keyword(self, extractor):
        """Test extracting season from 'Season N' format."""
        assert extractor.extract_season("Anime Name Season 3") == 3
        assert extractor.extract_season("Show season 5") == 5

    def test_extract_season_with_s_prefix(self, extractor):
        """Test extracting season from 'SN' format."""
        assert extractor.extract_season("Anime Name S2") == 2
        assert extractor.extract_season("Show S10") == 10

    def test_extract_season_number_at_end(self, extractor):
        """Test extracting season from number at end."""
        assert extractor.extract_season("Anime Name 4") == 4

    def test_extract_season_not_found(self, extractor):
        """Test default season when not found."""
        assert extractor.extract_season("Anime Name") == 1
        assert extractor.extract_season("") == 1

    def test_extract_year_from_meta(self, extractor):
        """Test extracting year from meta tag."""
        html = """
        <html>
        <head>
            <meta property="video:release_date" content="2023-01-15">
        </head>
        <body></body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        year = extractor.extract_year(soup)
        assert year == 2023

    def test_extract_year_from_content(self, extractor):
        """Test extracting year from page content."""
        html = """
        <html><body>
            <p>Released in 2024</p>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        year = extractor.extract_year(soup)
        assert year == 2024

    def test_extract_year_not_found(self, extractor):
        """Test None when year not found."""
        html = "<html><body>No year here</body></html>"
        soup = BeautifulSoup(html, "lxml")
        year = extractor.extract_year(soup)
        assert year is None

    def test_get_base_title_removes_season(self, extractor):
        """Test removing season from title."""
        assert extractor.get_base_title("Anime Name Season 3") == "Anime Name"
        assert extractor.get_base_title("Show S2") == "Show"
        assert extractor.get_base_title("Title 4") == "Title"

    def test_get_base_title_no_season(self, extractor):
        """Test title without season indicator."""
        assert extractor.get_base_title("Simple Anime Title") == "Simple Anime Title"


class TestEpisodeExtractor:
    """Test EpisodeExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return EpisodeExtractor()

    def test_extract_series_episodes(self, extractor):
        """Test extracting episodes for series with explicit player_id."""
        episode_items = [
            {"data_id": "0_0_0", "data_file": "https://ep1.com", "number": 1},
            {"data_id": "0_0_1", "data_file": "https://ep2.com", "number": 2},
            {"data_id": "0_1_0", "data_file": "https://other.com", "number": 1},
        ]
        all_items = [{"id": "0_0", "name": "Voice", "parts_count": 2}]

        # Use explicit player_id "0_0" to match episodes starting with "0_0"
        episodes = extractor.extract_episodes(
            episode_items=episode_items,
            voice_id="0",
            player_id="0_0",
            is_movie=False,
            all_items=all_items,
        )

        assert len(episodes) == 2
        assert episodes[0].data_file == "https://ep1.com"
        assert episodes[1].data_file == "https://ep2.com"

    def test_extract_series_episodes_with_player(self, extractor):
        """Test extracting episodes with specific player_id."""
        episode_items = [
            {"data_id": "0_0_0", "data_file": "https://ep1.com", "number": 1},
            {"data_id": "0_0_1", "data_file": "https://ep2.com", "number": 2},
            {"data_id": "0_1_0", "data_file": "https://other.com", "number": 1},
        ]
        all_items = []

        episodes = extractor.extract_episodes(
            episode_items=episode_items,
            voice_id="0",
            player_id="0_0",
            is_movie=False,
            all_items=all_items,
        )

        assert len(episodes) == 2
        assert all(ep.data_file.startswith("https://ep") for ep in episodes)

    def test_extract_movie_episodes_simple(self, extractor):
        """Test extracting movie episodes (simple structure)."""
        episode_items = [
            {"data_id": "0_0", "data_file": "https://movie.com"},
        ]
        all_items = [
            {"id": "0_0", "name": "ПЛЕЄР ASHDI", "parts_count": 2},
        ]

        episodes = extractor.extract_episodes(
            episode_items=episode_items,
            voice_id="0_0",
            player_id=None,
            is_movie=True,
            all_items=all_items,
        )

        assert len(episodes) == 1
        assert episodes[0].number == 1
        assert episodes[0].data_file == "https://movie.com"

    def test_extract_movie_episodes_complex(self, extractor):
        """Test extracting movie episodes (complex structure with voice/player)."""
        episode_items = [
            {"data_id": "0_0_0", "data_file": "https://movie1.com"},
            {"data_id": "0_1_0", "data_file": "https://movie2.com"},
        ]
        all_items = [
            {"id": "0_0", "name": "ТОНІС", "parts_count": 2},
            {"id": "0_0_0", "name": "ПЛЕЄР ASHDI", "parts_count": 3},
        ]

        episodes = extractor.extract_episodes(
            episode_items=episode_items,
            voice_id="0_0",
            player_id=None,
            is_movie=True,
            all_items=all_items,
        )

        assert len(episodes) == 1
        assert episodes[0].data_file == "https://movie1.com"

    def test_extract_episodes_skips_empty_file(self, extractor):
        """Test that episodes without data_file are skipped."""
        episode_items = [
            {"data_id": "0_0", "data_file": "https://valid.com"},
            {"data_id": "0_1", "data_file": ""},
        ]
        all_items = [{"id": "0_0", "name": "ПЛЕЄР", "parts_count": 2}]

        episodes = extractor.extract_episodes(
            episode_items=episode_items,
            voice_id="0_0",
            player_id=None,
            is_movie=True,
            all_items=all_items,
        )

        assert len(episodes) == 1

    def test_extract_series_direct_episodes(self, extractor):
        """Test series where voice_id matches episode data_id directly."""
        episode_items = [
            {"data_id": "0_0", "data_file": "https://ep1.com", "number": 1},
        ]
        all_items = []

        episodes = extractor.extract_episodes(
            episode_items=episode_items,
            voice_id="0_0",
            player_id=None,
            is_movie=False,
            all_items=all_items,
        )

        # Should find the episode with direct match
        assert len(episodes) == 1
