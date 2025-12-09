"""Shared fixtures for aniloader tests."""

import pytest

from aniloader.models import Anime, Episode, Voice, Player


@pytest.fixture
def anime_series() -> Anime:
    """Create a test anime (series) instance."""
    return Anime(
        news_id="1234",
        title_en="Test Anime",
        year=2024,
        season=1,
        is_movie=False,
    )


@pytest.fixture
def anime_movie() -> Anime:
    """Create a test anime (movie) instance."""
    return Anime(
        news_id="5678",
        title_en="Test Movie",
        year=2024,
        season=1,
        is_movie=True,
    )


@pytest.fixture
def episode() -> Episode:
    """Create a test episode instance."""
    return Episode(
        number=1,
        data_id="0_0",
        data_file="https://example.com/player/123",
    )


@pytest.fixture
def voice() -> Voice:
    """Create a test voice instance."""
    return Voice(id="0_0", name="Test Voice")


@pytest.fixture
def player() -> Player:
    """Create a test player instance."""
    return Player(id="0_0_0", name="Test Player")


@pytest.fixture
def mock_playlist_html():
    """Factory fixture to create mock playlist HTML."""

    def _create(
        players: list[tuple[str, str]], episodes: list[tuple[str, str, str]]
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

    return _create


@pytest.fixture
def mock_playerjs_html():
    """Factory fixture to create mock PlayerJS HTML."""

    def _create(file_value: str) -> str:
        return f"""
        <html>
        <script>
        Playerjs({{
            'file': '{file_value}'
        }})
        </script>
        </html>
        """

    return _create


@pytest.fixture
def mock_tortuga_html():
    """Factory fixture to create mock TortugaCore HTML."""
    import base64

    def _create(url: str) -> str:
        # TortugaCore encodes URLs as base64 + reversed string
        reversed_url = url[::-1]
        encoded = base64.b64encode(reversed_url.encode()).decode()
        return f"""
        <html>
        <script>
        new TortugaCore({{
            file: "{encoded}"
        }})
        </script>
        </html>
        """

    return _create
