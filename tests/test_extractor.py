"""Tests for extractor modules."""

import base64

import pytest
import responses

from aniloader.extraction.m3u8_extractor_refactored import M3U8Extractor
from aniloader.extraction.tortuga_extractor import TortugaCoreExtractor
from aniloader.extraction.playerjs_extractor import PlayerJSExtractor
from aniloader.extraction.extractor_chain import ExtractorChain
from aniloader.extraction.quality_selector import QualitySelector
from aniloader.models import Episode


class TestTortugaCoreExtractor:
    """Test TortugaCoreExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return TortugaCoreExtractor()

    def test_can_handle_true(self, extractor):
        """Test can_handle returns True for TortugaCore content."""
        html = '<script>new TortugaCore({file: "test"})</script>'
        assert extractor.can_handle(html) is True

    def test_can_handle_false(self, extractor):
        """Test can_handle returns False for non-TortugaCore content."""
        html = '<script>Playerjs({file: "test"})</script>'
        assert extractor.can_handle(html) is False

    def test_extract_url_success(self, extractor, mock_tortuga_html):
        """Test successful URL extraction from TortugaCore."""
        test_url = "https://example.com/video.m3u8"
        html = mock_tortuga_html(test_url)

        result = extractor.extract_url(html)
        assert result == test_url

    def test_extract_url_no_pattern(self, extractor):
        """Test extract_url returns None when no pattern found."""
        html = "<html><body>No TortugaCore here</body></html>"
        result = extractor.extract_url(html)
        assert result is None

    def test_extract_url_invalid_base64(self, extractor):
        """Test extract_url handles invalid base64 gracefully."""
        html = """
        <script>
        new TortugaCore({
            file: "not_valid_base64!!!"
        })
        </script>
        """
        result = extractor.extract_url(html)
        assert result is None

    def test_extract_url_normalizes_protocol(self, extractor):
        """Test that protocol-relative URLs are normalized."""
        # Create a URL without https: prefix (just //)
        test_url = "//example.com/video.m3u8"
        reversed_url = test_url[::-1]
        encoded = base64.b64encode(reversed_url.encode()).decode()

        html = f'''
        <script>
        new TortugaCore({{
            file: "{encoded}"
        }})
        </script>
        '''
        result = extractor.extract_url(html)
        assert result == "https://example.com/video.m3u8"


class TestPlayerJSExtractor:
    """Test PlayerJSExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return PlayerJSExtractor()

    def test_can_handle_true(self, extractor):
        """Test can_handle returns True for Playerjs content."""
        html = '<script>Playerjs({file: "test"})</script>'
        assert extractor.can_handle(html) is True

    def test_can_handle_false(self, extractor):
        """Test can_handle returns False for non-Playerjs content."""
        html = '<script>new TortugaCore({file: "test"})</script>'
        assert extractor.can_handle(html) is False

    def test_extract_url_simple(self, extractor):
        """Test extraction from simple Playerjs config."""
        html = """
        <script>
        Playerjs({
            "file": "https://example.com/video.m3u8"
        })
        </script>
        """
        result = extractor.extract_url(html)
        assert result == "https://example.com/video.m3u8"

    def test_extract_url_single_quotes(self, extractor):
        """Test extraction from Playerjs with single quotes."""
        html = """
        <script>
        Playerjs({
            'file': 'https://example.com/video.m3u8'
        })
        </script>
        """
        result = extractor.extract_url(html)
        assert result == "https://example.com/video.m3u8"

    def test_extract_url_no_pattern(self, extractor):
        """Test extract_url returns None when no pattern found."""
        html = "<html><body>No Playerjs here</body></html>"
        result = extractor.extract_url(html)
        assert result is None

    def test_extract_url_protocol_relative(self, extractor):
        """Test that protocol-relative URLs are normalized."""
        html = """
        <script>
        Playerjs({
            'file': '//cdn.example.com/video.m3u8'
        })
        </script>
        """
        result = extractor.extract_url(html)
        assert result == "https://cdn.example.com/video.m3u8"


class TestQualitySelector:
    """Test QualitySelector class."""

    @pytest.fixture
    def selector(self):
        """Create selector instance."""
        return QualitySelector()

    def test_select_best_quality_multi(self, selector):
        """Test selecting best quality from multiple options."""
        file_value = "[360p]https://example.com/360p.m3u8,[720p]https://example.com/720p.m3u8,[1080p]https://example.com/1080p.m3u8"
        result = selector.select_best_quality(file_value)
        assert result == "https://example.com/1080p.m3u8"

    def test_select_best_quality_single(self, selector):
        """Test that single quality URL is returned as-is."""
        file_value = "https://example.com/video.m3u8"
        result = selector.select_best_quality(file_value)
        assert result == file_value

    def test_select_best_quality_removes_trailing_slash(self, selector):
        """Test that trailing slashes are removed."""
        file_value = "[720p]https://example.com/720p.m3u8/,[1080p]https://example.com/1080p.m3u8/"
        result = selector.select_best_quality(file_value)
        assert result == "https://example.com/1080p.m3u8"
        assert not result.endswith("/")

    def test_select_best_quality_empty(self, selector):
        """Test that empty string returns empty string."""
        assert selector.select_best_quality("") == ""

    def test_select_best_quality_no_brackets(self, selector):
        """Test URL without quality markers is returned as-is."""
        file_value = "https://example.com/video.m3u8"
        result = selector.select_best_quality(file_value)
        assert result == file_value


class TestExtractorChain:
    """Test ExtractorChain class."""

    @pytest.fixture
    def chain(self):
        """Create extractor chain with both extractors."""
        return ExtractorChain(
            [
                TortugaCoreExtractor(),
                PlayerJSExtractor(),
            ]
        )

    def test_extract_tortuga_first(self, chain, mock_tortuga_html):
        """Test that TortugaCore is tried first."""
        test_url = "https://example.com/video.m3u8"
        html = mock_tortuga_html(test_url)

        result = chain.extract(html)
        assert result == test_url

    def test_extract_playerjs_fallback(self, chain, mock_playerjs_html):
        """Test that PlayerJS is used as fallback."""
        html = mock_playerjs_html("https://example.com/video.m3u8")

        result = chain.extract(html)
        assert result == "https://example.com/video.m3u8"

    def test_extract_none_no_match(self, chain):
        """Test that None is returned when no extractor matches."""
        html = "<html><body>No player here</body></html>"
        result = chain.extract(html)
        assert result is None

    def test_add_extractor(self, chain):
        """Test adding extractor to chain."""
        initial_count = len(chain.extractors)
        chain.add_extractor(PlayerJSExtractor())
        assert len(chain.extractors) == initial_count + 1


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
    def test_extract_m3u8_tortuga_player(self, extractor, episode, mock_tortuga_html):
        """Test extraction from TortugaCore player."""
        test_url = "https://example.com/test.m3u8"
        html = mock_tortuga_html(test_url)

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

    def test_extract_m3u8_no_data_file(self, extractor):
        """Test that None is returned when episode has no data_file."""
        episode = Episode(number=1, data_id="0_0", data_file="")
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
