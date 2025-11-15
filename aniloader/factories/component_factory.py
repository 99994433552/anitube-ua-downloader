"""Factory for creating application components with proper dependency injection."""

import logging

from ..scraper_refactored import AnitubeScraper
from ..core.http_client import HTTPClient
from ..parsing.html_parser import HTMLParser
from ..parsing.metadata_extractor import MetadataExtractor
from ..parsing.content_detector import ContentTypeDetector
from ..parsing.voice_extractor import VoiceExtractor
from ..parsing.episode_extractor import EpisodeExtractor

from ..extraction.m3u8_extractor_refactored import M3U8Extractor
from ..extraction.extractor_chain import ExtractorChain
from ..extraction.tortuga_extractor import TortugaCoreExtractor
from ..extraction.playerjs_extractor import PlayerJSExtractor
from ..extraction.quality_selector import QualitySelector

from ..downloading.video_downloader_refactored import VideoDownloader
from ..downloading.strategies.ytdlp_strategy import YtDlpStrategy
from ..downloading.filesystem import FileSystemManager
from ..downloading.filename_generator import FilenameGenerator

from ..cli.selector import InteractiveSelector
from ..cli.orchestrator import DownloadOrchestrator

logger = logging.getLogger(__name__)


class ComponentFactory:
    """Factory for creating application components with dependency injection."""

    @staticmethod
    def create_scraper() -> AnitubeScraper:
        """Create scraper with all dependencies.

        Returns:
            Configured AnitubeScraper instance
        """
        http_client = HTTPClient()
        html_parser = HTMLParser()
        metadata_extractor = MetadataExtractor()
        content_detector = ContentTypeDetector()
        voice_extractor = VoiceExtractor()
        episode_extractor = EpisodeExtractor()

        return AnitubeScraper(
            http_client=http_client,
            html_parser=html_parser,
            metadata_extractor=metadata_extractor,
            content_detector=content_detector,
            voice_extractor=voice_extractor,
            episode_extractor=episode_extractor,
        )

    @staticmethod
    def create_extractor(http_client: HTTPClient) -> M3U8Extractor:
        """Create M3U8 extractor with dependencies.

        Args:
            http_client: HTTP client instance (shared with scraper)

        Returns:
            Configured M3U8Extractor instance
        """
        # Create extractor chain with strategies
        extractors = [
            TortugaCoreExtractor(),  # Try newer player first
            PlayerJSExtractor(),  # Fallback to older player
        ]
        extractor_chain = ExtractorChain(extractors)
        quality_selector = QualitySelector()

        return M3U8Extractor(
            session=http_client.session,
            extractor_chain=extractor_chain,
            quality_selector=quality_selector,
        )

    @staticmethod
    def create_downloader(use_aria2c: bool = True) -> VideoDownloader:
        """Create video downloader with dependencies.

        Args:
            use_aria2c: Whether to use aria2c acceleration

        Returns:
            Configured VideoDownloader instance
        """
        download_strategy = YtDlpStrategy(use_aria2c_downloader=use_aria2c)
        fs_manager = FileSystemManager()
        filename_generator = FilenameGenerator()

        return VideoDownloader(
            download_strategy=download_strategy,
            fs_manager=fs_manager,
            filename_generator=filename_generator,
        )

    @staticmethod
    def create_orchestrator(use_aria2c: bool = True) -> DownloadOrchestrator:
        """Create download orchestrator with all dependencies.

        Args:
            use_aria2c: Whether to use aria2c acceleration

        Returns:
            Configured DownloadOrchestrator instance
        """
        # Create scraper (will create its own HTTP client internally)
        scraper = ComponentFactory.create_scraper()

        # Create extractor (share session with scraper)
        extractor = ComponentFactory.create_extractor(scraper.http_client)

        # Create downloader
        downloader = ComponentFactory.create_downloader(use_aria2c=use_aria2c)

        # Create selector
        selector = InteractiveSelector()

        # Create orchestrator
        return DownloadOrchestrator(
            scraper=scraper,
            extractor=extractor,
            downloader=downloader,
            selector=selector,
        )
