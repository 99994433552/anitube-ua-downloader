"""Download orchestrator coordinating the entire download process."""

import logging
from typing import Optional

from ..downloading.video_downloader_refactored import VideoDownloader
from ..extraction.m3u8_extractor_refactored import M3U8Extractor
from ..scraper_refactored import AnitubeScraper
from .selector import InteractiveSelector

logger = logging.getLogger(__name__)


class DownloadOrchestrator:
    """Orchestrator for the download process using dependency injection."""

    def __init__(
        self,
        scraper: AnitubeScraper,
        extractor: M3U8Extractor,
        downloader: VideoDownloader,
        selector: InteractiveSelector,
    ):
        """Initialize orchestrator with dependencies.

        Args:
            scraper: Anime scraper
            extractor: M3U8 URL extractor
            downloader: Video downloader
            selector: Interactive selector
        """
        self.scraper = scraper
        self.extractor = extractor
        self.downloader = downloader
        self.selector = selector

    def run(
        self,
        url: str,
        voice_index: Optional[int] = None,
        title: Optional[str] = None,
        output_dir: str = ".",
    ) -> dict[str, int]:
        """Run the complete download process.

        Args:
            url: Anime URL
            voice_index: Optional voice index (1-based)
            title: Optional custom title
            output_dir: Output directory path

        Returns:
            Statistics dictionary with successful/failed counts
        """
        # Step 1: Fetch anime metadata
        print(f"\nFetching anime metadata from {url}...")
        anime = self.scraper.fetch_anime_metadata(url)

        # Override title if provided
        if title:
            anime.title_en = title
            print(f"Using custom title: {title}")

        # Display anime info
        content_type = "movie" if anime.is_movie else "series"
        print(f"\n{anime.title_en} - {content_type}")
        if anime.year:
            print(f"Year: {anime.year}")
        if not anime.is_movie:
            print(f"Season: {anime.season}")

        # Step 2: Voice selection
        if not anime.voices:
            print("No voices/players found!")
            return {"successful": 0, "failed": 0}

        print(
            f"\nFound {len(anime.voices)} {'player' if anime.is_movie else 'voice'} options"
        )

        # Select voice
        if voice_index is not None:
            # Use provided voice index
            if 1 <= voice_index <= len(anime.voices):
                voice = anime.voices[voice_index - 1]
                print(f"Using {'player' if anime.is_movie else 'voice'}: {voice.name}")
            else:
                print(
                    f"Invalid voice index {voice_index}. Please use 1-{len(anime.voices)}"
                )
                return {"successful": 0, "failed": 0}
        else:
            # Interactive selection
            voice = self.selector.select_voice(anime.voices)

        voice_id = voice.id

        # Step 3: Player selection (if needed for series)
        player_id = None
        if not anime.is_movie:
            # Get players for selected voice
            players = self.scraper.get_available_players(anime, voice_id)

            if players:
                print(f"\nFound {len(players)} player options for this voice")
                player = self.selector.select_player(players)
                player_id = player.id

        # Step 4: Fetch episodes for selected voice/player
        print("\nFetching episode list...")
        anime = self.scraper.fetch_playlist(
            anime, voice_id=voice_id, player_id=player_id
        )

        if not anime.episodes:
            print("No episodes found!")
            return {"successful": 0, "failed": 0}

        print(f"Found {len(anime.episodes)} episodes")

        # Step 5: Extract m3u8 URLs
        print("\nExtracting video URLs...")
        anime.episodes = self.extractor.extract_all_m3u8_urls(anime.episodes)

        # Filter episodes with successful extraction
        episodes_to_download = [ep for ep in anime.episodes if ep.m3u8_url]

        if not episodes_to_download:
            print("Failed to extract any video URLs!")
            return {"successful": 0, "failed": 0}

        print(
            f"Successfully extracted {len(episodes_to_download)}/{len(anime.episodes)} URLs"
        )

        # Step 6: Create output directory
        output_path = self.downloader.create_output_directory(anime, output_dir)
        print(f"\nOutput directory: {output_path}")

        # Step 7: Download episodes
        print(f"\nDownloading {len(episodes_to_download)} episodes...")

        successful = 0
        failed = 0

        for episode in episodes_to_download:
            print(f"\n[{episode.number}/{len(episodes_to_download)}] ", end="")
            success, message = self.downloader.download_episode(
                anime, episode, output_path
            )

            if success:
                successful += 1
            else:
                failed += 1
                print(f"  Error: {message}")

        # Step 8: Show summary
        print("\n" + "=" * 50)
        print("Download complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print("=" * 50)

        return {"successful": successful, "failed": failed}
