"""HTTP client with session management for anitube.in.ua."""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client for making requests to anitube.in.ua with proper headers."""

    BASE_URL = "https://anitube.in.ua"
    AJAX_PLAYLIST_URL = f"{BASE_URL}/engine/ajax/playlists.php"

    def __init__(self):
        """Initialize HTTP client with configured session."""
        self._session = requests.Session()
        self._configure_session()

    def _configure_session(self) -> None:
        """Configure session with headers needed to bypass Cloudflare."""
        self._session.headers.update(
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

    @property
    def session(self) -> requests.Session:
        """Get the underlying requests session."""
        return self._session

    def get(self, url: str, **kwargs) -> requests.Response:
        """Perform GET request.

        Args:
            url: URL to fetch
            **kwargs: Additional arguments passed to requests.get

        Returns:
            Response object

        Raises:
            requests.HTTPError: If request fails
        """
        logger.debug(f"GET request to {url}")
        response = self._session.get(url, **kwargs)
        response.raise_for_status()
        return response

    def post(
        self, url: str, data: Optional[dict] = None, **kwargs
    ) -> requests.Response:
        """Perform POST request.

        Args:
            url: URL to post to
            data: POST data
            **kwargs: Additional arguments passed to requests.post

        Returns:
            Response object

        Raises:
            requests.HTTPError: If request fails
        """
        logger.debug(f"POST request to {url}")
        response = self._session.post(url, data=data, **kwargs)
        response.raise_for_status()
        return response

    def ajax_playlist_request(self, news_id: str, user_hash: str, referer: str) -> str:
        """Make AJAX request for playlist data.

        Args:
            news_id: Anime news ID
            user_hash: User hash extracted from page
            referer: Referer URL for the request

        Returns:
            HTML response from AJAX endpoint
        """
        data = {
            "news_id": news_id,
            "xfield": "playlist",
            "user_hash": user_hash,
        }
        headers = {
            "Referer": referer,
            "X-Requested-With": "XMLHttpRequest",
        }
        logger.debug(f"AJAX playlist request for news_id={news_id}")
        response = self.post(self.AJAX_PLAYLIST_URL, data=data, headers=headers)
        return response.text
