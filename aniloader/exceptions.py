"""Custom exceptions for aniloader."""


class AniloaderError(Exception):
    """Base exception for aniloader."""

    pass


class NoVoicesError(AniloaderError):
    """Raised when no voice options are available."""

    pass


class NoPlayersError(AniloaderError):
    """Raised when no player options are available."""

    pass


class UserCancelledError(AniloaderError):
    """Raised when user cancels operation (e.g., KeyboardInterrupt)."""

    pass


class ExtractionError(AniloaderError):
    """Raised when video URL extraction fails."""

    pass


class DownloadError(AniloaderError):
    """Raised when download fails."""

    pass
