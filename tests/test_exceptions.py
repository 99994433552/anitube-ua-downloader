"""Tests for exceptions module."""

import pytest

from aniloader.exceptions import (
    AniloaderError,
    NoVoicesError,
    NoPlayersError,
    UserCancelledError,
    ExtractionError,
    DownloadError,
)


class TestExceptions:
    """Test custom exceptions."""

    def test_aniloader_error_is_base_exception(self):
        """Test AniloaderError is base for all custom exceptions."""
        assert issubclass(NoVoicesError, AniloaderError)
        assert issubclass(NoPlayersError, AniloaderError)
        assert issubclass(UserCancelledError, AniloaderError)
        assert issubclass(ExtractionError, AniloaderError)
        assert issubclass(DownloadError, AniloaderError)

    def test_no_voices_error_message(self):
        """Test NoVoicesError can be raised with message."""
        with pytest.raises(NoVoicesError) as exc_info:
            raise NoVoicesError("No voices found")
        assert "No voices found" in str(exc_info.value)

    def test_no_players_error_message(self):
        """Test NoPlayersError can be raised with message."""
        with pytest.raises(NoPlayersError) as exc_info:
            raise NoPlayersError("No players found")
        assert "No players found" in str(exc_info.value)

    def test_user_cancelled_error_message(self):
        """Test UserCancelledError can be raised with message."""
        with pytest.raises(UserCancelledError) as exc_info:
            raise UserCancelledError("Cancelled by user")
        assert "Cancelled by user" in str(exc_info.value)

    def test_extraction_error_message(self):
        """Test ExtractionError can be raised with message."""
        with pytest.raises(ExtractionError) as exc_info:
            raise ExtractionError("Failed to extract URL")
        assert "Failed to extract URL" in str(exc_info.value)

    def test_download_error_message(self):
        """Test DownloadError can be raised with message."""
        with pytest.raises(DownloadError) as exc_info:
            raise DownloadError("Download failed")
        assert "Download failed" in str(exc_info.value)

    def test_exceptions_can_be_caught_by_base(self):
        """Test all exceptions can be caught by AniloaderError."""
        exceptions = [
            NoVoicesError("test"),
            NoPlayersError("test"),
            UserCancelledError("test"),
            ExtractionError("test"),
            DownloadError("test"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except AniloaderError as e:
                assert str(e) == "test"
