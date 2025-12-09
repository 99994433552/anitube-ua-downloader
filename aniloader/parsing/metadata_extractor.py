"""Metadata extraction from anime pages."""

import re
import logging
import urllib.parse
from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extractor for anime metadata from HTML pages."""

    def extract_news_id(self, url: str) -> str:
        """Extract news ID from anime URL.

        Args:
            url: Anime page URL

        Returns:
            News ID string

        Raises:
            ValueError: If news_id cannot be extracted
        """
        match = re.search(r"/(\d+)-.*\.html", url)
        if not match:
            raise ValueError(f"Could not extract news_id from URL: {url}")
        return match.group(1)

    def extract_user_hash(self, html: str) -> str:
        """Extract user hash from HTML page.

        Args:
            html: Page HTML content

        Returns:
            User hash string (empty if not found)
        """
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

    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extract English title from page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            English title (or "Unknown" if not found)
        """
        # Extract English title from Twitter share link
        # Format: "Українська назва / English Name https://..."
        twitter_link = soup.find("a", href=re.compile(r"twitter\.com/intent/tweet"))
        if twitter_link:
            href = str(twitter_link.get("href", ""))
            # Extract text parameter from URL
            match = re.search(r"text=([^&]+)", href)
            if match:
                decoded_text = urllib.parse.unquote(match.group(1))
                # Split by " / " and take English part
                if " / " in decoded_text:
                    parts = decoded_text.split(" / ")
                    if len(parts) >= 2:
                        # Remove URL at the end (everything after http)
                        english_part = re.sub(r"\s*https?://.*$", "", parts[1])
                        title_en = english_part.strip()
                        if title_en:
                            return title_en

        # Fallback to og:title if English name not found
        title_tag = (
            soup.find("meta", property="og:title")
            or soup.find("h1", class_="title")
            or soup.find("h1")
        )

        if title_tag:
            # Meta tags have content attribute, h1 tags need get_text
            if title_tag.name == "meta":
                content = title_tag.get("content")
                title_text = str(content) if content else ""
            else:
                title_text = title_tag.get_text(strip=True)

            if title_text:
                return str(title_text)

        return "Unknown"

    def extract_season(self, title: str) -> int:
        """Extract season number from title.

        Args:
            title: Anime title

        Returns:
            Season number (defaults to 1 if not found)
        """
        # Patterns: "Name 3", "Name Season 4", "Name S2"
        patterns = [
            r"\bSeason\s+(\d+)\b",
            r"\bS(\d+)\b",
            r"\s+(\d+)$",  # Number at end of title
        ]

        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                season_num = int(match.group(1))
                if season_num > 0:
                    logger.debug(f"Extracted season {season_num} from title: {title}")
                    return season_num

        logger.debug(f"No season found in title, defaulting to 1: {title}")
        return 1

    def extract_year(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract release year from page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Release year or None if not found
        """
        # Look for year in various possible locations
        # 1. In meta tags
        year_meta = soup.find("meta", property="video:release_date")
        if year_meta and hasattr(year_meta, "get"):
            content = year_meta.get("content")
            if content:
                year_str = str(content)
                match = re.search(r"(\d{4})", year_str)
                if match:
                    return int(match.group(1))

        # 2. In page content (look for 4-digit year)
        content = soup.get_text()
        year_matches = re.findall(r"\b(20\d{2})\b", content)
        if year_matches:
            # Take the most common year or the first one
            return int(year_matches[0])

        return None

    def get_base_title(self, title: str) -> str:
        """Remove season indicators from title to get base name.

        Args:
            title: Full title with possible season indicator

        Returns:
            Base title without season number
        """
        # Remove patterns like " 3", " Season 4", " S2" from end
        patterns = [
            r"\s+Season\s+\d+$",
            r"\s+S\d+$",
            r"\s+\d+$",
        ]

        base_title = title
        for pattern in patterns:
            base_title = re.sub(pattern, "", base_title, flags=re.IGNORECASE)

        return base_title.strip()
