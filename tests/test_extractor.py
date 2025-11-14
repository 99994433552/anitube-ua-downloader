"""Tests for extractor module."""

import pytest
import responses

from aniloader.extractor import M3U8Extractor
from aniloader.models import Episode


class TestM3U8Extractor:
    """Test M3U8Extractor class."""

    @pytest.fixture
    def extractor(self):
        """Create M3U8Extractor instance."""
        return M3U8Extractor()

    @pytest.fixture
    def episode(self):
        """Create test episode."""
        return Episode(
            number=1,
            data_id="0_0",
            data_file="https://example.com/player/123",
        )

    @responses.activate
    def test_extract_m3u8_playerjs_simple(self, extractor, episode):
        """Test extraction from simple Playerjs config."""
        html = """
        <script>
        Playerjs({
            "file": "https://example.com/video.m3u8"
        })
        </script>
        """
        responses.add(
            responses.GET,
            episode.data_file,
            body=html,
            status=200,
        )

        m3u8_url = extractor.extract_m3u8_url(episode)
        assert m3u8_url == "https://example.com/video.m3u8"

    @responses.activate
    def test_extract_m3u8_playerjs_single_quotes(self, extractor, episode):
        """Test extraction from Playerjs with single quotes."""
        html = """
        <script>
        Playerjs({
            'file': 'https://example.com/video.m3u8'
        })
        </script>
        """
        responses.add(
            responses.GET,
            episode.data_file,
            body=html,
            status=200,
        )

        m3u8_url = extractor.extract_m3u8_url(episode)
        assert m3u8_url == "https://example.com/video.m3u8"

    @responses.activate
    def test_extract_m3u8_multi_quality(self, extractor, episode):
        """Test extraction from multi-quality format."""
        html = """
        <script>
        Playerjs({
            'file': '[360p]https://example.com/360p.m3u8,[720p]https://example.com/720p.m3u8,[1080p]https://example.com/1080p.m3u8'
        })
        </script>
        """
        responses.add(
            responses.GET,
            episode.data_file,
            body=html,
            status=200,
        )

        m3u8_url = extractor.extract_m3u8_url(episode)
        # Should select highest quality (1080p)
        assert m3u8_url == "https://example.com/1080p.m3u8"

    @responses.activate
    def test_extract_m3u8_relative_url(self, extractor, episode):
        """Test extraction with relative URL that needs protocol."""
        html = """
        <script>
        Playerjs({
            'file': '//cdn.example.com/video.m3u8'
        })
        </script>
        """
        responses.add(
            responses.GET,
            episode.data_file,
            body=html,
            status=200,
        )

        m3u8_url = extractor.extract_m3u8_url(episode)
        assert m3u8_url == "https://cdn.example.com/video.m3u8"

    @responses.activate
    def test_extract_m3u8_tortuga_player(self, extractor, episode):
        """Test extraction from TortugaCore player."""
        # TortugaCore uses base64 encoded reversed string
        # "test.m3u8" reversed = "8u3m.tset" -> base64
        import base64

        test_url = "https://example.com/test.m3u8"
        reversed_url = test_url[::-1]
        encoded = base64.b64encode(reversed_url.encode()).decode()

        html = f"""
        <script>
        new TortugaCore({{
            file: "{encoded}"
        }})
        </script>
        """
        responses.add(
            responses.GET,
            episode.data_file,
            body=html,
            status=200,
        )

        m3u8_url = extractor.extract_m3u8_url(episode)
        assert m3u8_url == test_url

    @responses.activate
    def test_extract_m3u8_no_player_config(self, extractor, episode):
        """Test that None is returned when no player config found."""
        html = """
        <html>
        <body>
            <p>No player here</p>
        </body>
        </html>
        """
        responses.add(
            responses.GET,
            episode.data_file,
            body=html,
            status=200,
        )

        m3u8_url = extractor.extract_m3u8_url(episode)
        assert m3u8_url is None

    @responses.activate
    def test_extract_m3u8_empty_response(self, extractor, episode):
        """Test that None is returned for empty response."""
        responses.add(
            responses.GET,
            episode.data_file,
            body="",
            status=200,
        )

        m3u8_url = extractor.extract_m3u8_url(episode)
        assert m3u8_url is None

    @responses.activate
    def test_extract_all_m3u8_urls(self, extractor):
        """Test extraction for multiple episodes."""
        episodes = [
            Episode(number=1, data_id="0_0", data_file="https://example.com/ep1"),
            Episode(number=2, data_id="0_0", data_file="https://example.com/ep2"),
            Episode(number=3, data_id="0_0", data_file="https://example.com/ep3"),
        ]

        # Mock responses for all episodes
        for i, ep in enumerate(episodes, 1):
            html = f"""
            <script>
            Playerjs({{
                "file": "https://example.com/video{i}.m3u8"
            }})
            </script>
            """
            responses.add(
                responses.GET,
                ep.data_file,
                body=html,
                status=200,
            )

        result = extractor.extract_all_m3u8_urls(episodes)

        assert len(result) == 3
        assert result[0].m3u8_url == "https://example.com/video1.m3u8"
        assert result[1].m3u8_url == "https://example.com/video2.m3u8"
        assert result[2].m3u8_url == "https://example.com/video3.m3u8"

    @responses.activate
    def test_extract_best_quality_url_with_trailing_slash(self, extractor, episode):
        """Test that trailing slashes are removed from quality URLs."""
        html = """
        <script>
        Playerjs({
            'file': '[720p]https://example.com/720p.m3u8/,[1080p]https://example.com/1080p.m3u8/'
        })
        </script>
        """
        responses.add(
            responses.GET,
            episode.data_file,
            body=html,
            status=200,
        )

        m3u8_url = extractor.extract_m3u8_url(episode)
        # Should select 1080p and remove trailing slash
        assert m3u8_url == "https://example.com/1080p.m3u8"
        assert not m3u8_url.endswith("/")
