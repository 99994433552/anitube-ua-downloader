"""Factory for creating application components."""

from ..scraper_refactored import AnitubeScraper
from ..extraction.m3u8_extractor_refactored import M3U8Extractor
from ..downloading.video_downloader_refactored import VideoDownloader
from ..downloading.strategies.ytdlp_strategy import YtDlpStrategy
from ..cli.selector import InteractiveSelector
from ..cli.orchestrator import DownloadOrchestrator


def create_orchestrator(use_aria2c: bool = True) -> DownloadOrchestrator:
    """Create download orchestrator with all dependencies.

    Args:
        use_aria2c: Whether to use aria2c acceleration

    Returns:
        Configured DownloadOrchestrator instance
    """
    scraper = AnitubeScraper()
    extractor = M3U8Extractor(session=scraper.http_client.session)
    downloader = VideoDownloader(
        download_strategy=YtDlpStrategy(use_aria2c_downloader=use_aria2c)
    )
    selector = InteractiveSelector()

    return DownloadOrchestrator(
        scraper=scraper,
        extractor=extractor,
        downloader=downloader,
        selector=selector,
    )
