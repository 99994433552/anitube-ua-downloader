"""Tests for downloader modules."""

import pytest

from aniloader.downloading.filesystem import sanitize_filename, FileSystemManager
from aniloader.downloading.filename_generator import FilenameGenerator
from aniloader.downloading.video_downloader_refactored import VideoDownloader
from aniloader.models import Anime, Episode


class TestSanitizeFilename:
    """Test sanitize_filename function."""

    def test_colon_replacement(self):
        """Test that colons are replaced with space-dash."""
        assert sanitize_filename("Book 1: Water") == "Book 1 - Water"
        assert (
            sanitize_filename("Avatar: The Last Airbender")
            == "Avatar - The Last Airbender"
        )

    def test_slash_replacement(self):
        """Test that slashes are replaced with dash."""
        assert sanitize_filename("Title/with/slashes") == "Title-with-slashes"
        assert sanitize_filename("Title\\with\\backslashes") == "Title-with-backslashes"

    def test_pipe_replacement(self):
        """Test that pipes are replaced with dash."""
        assert sanitize_filename("Title|with|pipes") == "Title-with-pipes"

    def test_question_mark_removal(self):
        """Test that question marks are removed."""
        assert sanitize_filename("Title?with?questions") == "Titlewithquestions"

    def test_asterisk_removal(self):
        """Test that asterisks are removed."""
        assert sanitize_filename("Title*with*asterisks") == "Titlewithasterisks"

    def test_bracket_removal(self):
        """Test that angle brackets are removed."""
        assert sanitize_filename("Title<with>brackets") == "Titlewithbrackets"

    def test_quote_replacement(self):
        """Test that double quotes are replaced with single quotes."""
        assert sanitize_filename('Title"with"quotes') == "Title'with'quotes"

    def test_leading_trailing_spaces(self):
        """Test that leading/trailing spaces are removed."""
        assert sanitize_filename("  Leading spaces  ") == "Leading spaces"

    def test_trailing_dots(self):
        """Test that trailing dots are removed."""
        assert sanitize_filename("Trailing dots...") == "Trailing dots"

    def test_multiple_spaces_collapse(self):
        """Test that multiple spaces are collapsed to single space."""
        assert sanitize_filename("Multiple   spaces   here") == "Multiple spaces here"

    def test_complex_filename(self):
        """Test complex filename with multiple problematic characters."""
        input_name = "Avatar: The Last Airbender / Book 1: Water (2025)"
        expected = "Avatar - The Last Airbender - Book 1 - Water (2025)"
        assert sanitize_filename(input_name) == expected

    def test_empty_string(self):
        """Test that empty string returns empty string."""
        assert sanitize_filename("") == ""

    def test_no_invalid_characters(self):
        """Test that valid filenames are unchanged."""
        assert sanitize_filename("ValidFilename.mp4") == "ValidFilename.mp4"
        assert sanitize_filename("Series Name S01E01") == "Series Name S01E01"


class TestFilenameGenerator:
    """Test FilenameGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create a FilenameGenerator instance."""
        return FilenameGenerator()

    def test_generate_episode_filename_series(self, generator, anime_series):
        """Test filename generation for series episodes."""
        episode = Episode(number=1, data_id="0_0", data_file="test.m3u8")
        filename = generator.generate_episode_filename(anime_series, episode)
        assert filename == "Test Anime S01E01.mp4"

    def test_generate_episode_filename_series_double_digit(
        self, generator, anime_series
    ):
        """Test filename generation for series with double-digit episode."""
        episode = Episode(number=12, data_id="0_0", data_file="test.m3u8")
        filename = generator.generate_episode_filename(anime_series, episode)
        assert filename == "Test Anime S01E12.mp4"

    def test_generate_episode_filename_series_season_2(self, generator, anime_series):
        """Test filename generation for series season 2."""
        anime_series.season = 2
        episode = Episode(number=5, data_id="0_0", data_file="test.m3u8")
        filename = generator.generate_episode_filename(anime_series, episode)
        assert filename == "Test Anime S02E05.mp4"

    def test_generate_episode_filename_movie_with_year(self, generator, anime_movie):
        """Test filename generation for movie with year."""
        episode = Episode(number=1, data_id="0_0", data_file="test.m3u8")
        filename = generator.generate_episode_filename(anime_movie, episode)
        assert filename == "Test Movie (2024).mp4"

    def test_generate_episode_filename_movie_without_year(self, generator):
        """Test filename generation for movie without year."""
        anime = Anime(
            news_id="5678",
            title_en="Test Movie",
            year=None,
            season=1,
            is_movie=True,
        )
        episode = Episode(number=1, data_id="0_0", data_file="test.m3u8")
        filename = generator.generate_episode_filename(anime, episode)
        assert filename == "Test Movie.mp4"

    def test_generate_filename_with_invalid_characters(self, generator, anime_series):
        """Test that invalid characters are sanitized in filenames."""
        anime_series.title_en = "Avatar: The Last Airbender"
        episode = Episode(number=1, data_id="0_0", data_file="test.m3u8")
        filename = generator.generate_episode_filename(anime_series, episode)
        assert filename == "Avatar - The Last Airbender S01E01.mp4"
        assert ":" not in filename


class TestFileSystemManager:
    """Test FileSystemManager class."""

    @pytest.fixture
    def fs_manager(self):
        """Create a FileSystemManager instance."""
        return FileSystemManager()

    def test_create_output_directory_series(self, fs_manager, anime_series, tmp_path):
        """Test output directory creation for series."""
        output_dir = fs_manager.create_output_directory(anime_series, str(tmp_path))
        expected_path = tmp_path / "Test Anime" / "Season 01"
        assert output_dir == expected_path
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_create_output_directory_movie_with_year(
        self, fs_manager, anime_movie, tmp_path
    ):
        """Test output directory creation for movie with year."""
        output_dir = fs_manager.create_output_directory(anime_movie, str(tmp_path))
        expected_path = tmp_path / "Test Movie (2024)"
        assert output_dir == expected_path
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_create_output_directory_with_invalid_chars(self, fs_manager, tmp_path):
        """Test that invalid characters are sanitized in directory names."""
        anime = Anime(
            news_id="1234",
            title_en="Avatar: The Last Airbender",
            year=2024,
            season=1,
            is_movie=False,
        )
        output_dir = fs_manager.create_output_directory(anime, str(tmp_path))
        expected_path = tmp_path / "Avatar - The Last Airbender" / "Season 01"
        assert output_dir == expected_path
        assert ":" not in str(output_dir)

    def test_file_exists_true(self, fs_manager, tmp_path):
        """Test file_exists returns True for existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        assert fs_manager.file_exists(test_file) is True

    def test_file_exists_false_not_exists(self, fs_manager, tmp_path):
        """Test file_exists returns False for non-existing file."""
        test_file = tmp_path / "nonexistent.txt"
        assert fs_manager.file_exists(test_file) is False

    def test_file_exists_false_for_directory(self, fs_manager, tmp_path):
        """Test file_exists returns False for directory."""
        assert fs_manager.file_exists(tmp_path) is False


class TestVideoDownloader:
    """Test VideoDownloader class."""

    @pytest.fixture
    def downloader(self):
        """Create a VideoDownloader instance."""
        return VideoDownloader()

    def test_generate_episode_filename_delegates(self, downloader, anime_series):
        """Test that generate_episode_filename delegates to generator."""
        episode = Episode(number=1, data_id="0_0", data_file="test.m3u8")
        filename = downloader.generate_episode_filename(anime_series, episode)
        assert filename == "Test Anime S01E01.mp4"

    def test_create_output_directory_delegates(
        self, downloader, anime_series, tmp_path
    ):
        """Test that create_output_directory delegates to fs_manager."""
        output_dir = downloader.create_output_directory(anime_series, str(tmp_path))
        assert output_dir.exists()

    def test_download_episode_no_m3u8_url(self, downloader, anime_series, tmp_path):
        """Test download_episode fails gracefully when no m3u8_url."""
        episode = Episode(number=1, data_id="0_0", data_file="test.m3u8", m3u8_url=None)
        success, message = downloader.download_episode(anime_series, episode, tmp_path)
        assert success is False
        assert "no m3u8_url" in message

    def test_download_episode_skips_existing(self, downloader, anime_series, tmp_path):
        """Test download_episode skips already existing files."""
        episode = Episode(
            number=1,
            data_id="0_0",
            data_file="test.m3u8",
            m3u8_url="https://example.com/video.m3u8",
        )
        # Create the file
        output_dir = downloader.create_output_directory(anime_series, str(tmp_path))
        filename = downloader.generate_episode_filename(anime_series, episode)
        (output_dir / filename).write_text("existing")

        success, message = downloader.download_episode(
            anime_series, episode, output_dir
        )
        assert success is True
        assert "already exists" in message
