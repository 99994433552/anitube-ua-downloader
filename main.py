"""CLI interface for aniloader."""

import sys
import argparse
import logging

from aniloader.scraper import AnitubeScraper
from aniloader.extractor import M3U8Extractor
from aniloader.downloader import VideoDownloader
from aniloader.models import Anime


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def select_voice_interactive(anime: Anime) -> str:
    """Prompt user to select a voice option."""
    if not anime.voices:
        print("No voice options found!")
        sys.exit(1)

    if len(anime.voices) == 1:
        print(f"Using only available voice: {anime.voices[0].name}")
        return anime.voices[0].id

    print("\nAvailable voice options:")
    for idx, voice in enumerate(anime.voices, start=1):
        print(f"  {idx}. {voice.name}")

    while True:
        try:
            choice = input("\nSelect voice option (number): ").strip()
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(anime.voices):
                selected = anime.voices[choice_idx]
                print(f"Selected: {selected.name}")
                return selected.id
            else:
                print(f"Invalid choice. Please enter 1-{len(anime.voices)}")

        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nCancelled by user")
            sys.exit(0)


def select_player_interactive(players: list) -> str:
    """Prompt user to select a player option."""
    if not players:
        print("No players found!")
        sys.exit(1)

    if len(players) == 1:
        print(f"Using only available player: {players[0].name}")
        return players[0].id

    print("\nAvailable players:")
    for idx, player in enumerate(players, start=1):
        print(f"  {idx}. {player.name}")

    while True:
        try:
            choice = input("\nSelect player (number, or Enter for first): ").strip()

            # Allow empty input to select first player
            if not choice:
                selected = players[0]
                print(f"Selected: {selected.name}")
                return selected.id

            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(players):
                selected = players[choice_idx]
                print(f"Selected: {selected.name}")
                return selected.id
            else:
                print(f"Invalid choice. Please enter 1-{len(players)}")

        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nCancelled by user")
            sys.exit(0)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download anime episodes from anitube.in.ua",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (interactive voice selection)
  python main.py https://anitube.in.ua/4110-lyudina-benzopila.html

  # Specify output directory
  python main.py <URL> --output ~/Downloads/Anime

  # Specify voice ID (to skip interactive selection)
  python main.py <URL> --voice 1

  # Disable aria2c acceleration
  python main.py <URL> --no-aria2c

  # Verbose logging
  python main.py <URL> --verbose
        """,
    )

    parser.add_argument("url", help="URL to anime page on anitube.in.ua")
    parser.add_argument(
        "--output",
        "-o",
        default=".",
        help="Output directory for downloaded episodes (default: current directory)",
    )
    parser.add_argument(
        "--voice",
        help="Voice/dub ID to use (if not specified, will prompt interactively)",
    )
    parser.add_argument(
        "--title",
        help="Override anime title (useful when auto-detection returns Ukrainian name)",
    )
    parser.add_argument(
        "--no-aria2c",
        action="store_true",
        help="Disable aria2c acceleration (use default yt-dlp downloader)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Initialize components
        scraper = AnitubeScraper()
        extractor = M3U8Extractor(session=scraper.session)
        downloader = VideoDownloader(use_aria2c=not args.no_aria2c)

        # Step 1: Fetch anime metadata
        print(f"\nFetching anime metadata from {args.url}...")
        anime = scraper.fetch_anime_metadata(args.url)

        # Override title if provided
        if args.title:
            anime.title_en = args.title
            print(
                f"Using custom title: {anime.title_en}"
                + (f" ({anime.year})" if anime.year else "")
            )
        else:
            print(
                f"Found: {anime.title_en}" + (f" ({anime.year})" if anime.year else "")
            )

        # Step 2: Fetch playlist to get available voices/players
        print("\nFetching content...")
        anime = scraper.fetch_playlist(anime)

        # Now we can detect content type (set in fetch_playlist)
        content_type = "movie" if anime.is_movie else "series"
        print(f"Detected content type: {content_type}")

        if anime.is_movie:
            print(f"Found {len(anime.voices)} player options")
        else:
            print(f"Found {len(anime.voices)} voice options")

        # Step 3: Select voice/player
        selected_voice_id = args.voice
        if selected_voice_id:
            # User provided voice index (1-based), convert to data-id
            try:
                voice_idx = int(selected_voice_id) - 1
                if 0 <= voice_idx < len(anime.voices):
                    selected_voice_id = anime.voices[voice_idx].id
                else:
                    print(
                        f"Invalid {'player' if anime.is_movie else 'voice'} "
                        f"index: {args.voice}. "
                        f"Must be 1-{len(anime.voices)}"
                    )
                    sys.exit(1)
            except ValueError:
                # Maybe it's already a data-id, use as-is
                pass
        else:
            selected_voice_id = select_voice_interactive(anime)

        # Step 4-6: Get players for both series and complex movies
        print("\nFetching available players...")
        players = scraper.get_available_players(anime, selected_voice_id)

        if not players:
            # No players found - voice IS the player (simple structure for both movies and series)
            selected_player_id = None
            print("No separate players, using selected voice as player")
            anime = scraper.fetch_playlist(
                anime, voice_id=selected_voice_id, player_id=None
            )
            if anime.is_movie:
                print("Found movie file")
            else:
                print(f"Found {anime.total_episodes} episodes")
        else:
            # Players found - select one (for both series and complex movies)
            selected_player_id = select_player_interactive(players)

            # Fetch episodes for selected voice and player
            content_label = (
                "movie"
                if anime.is_movie
                else f"{anime.total_episodes if anime.total_episodes else '?'} episodes"
            )
            print(f"\nFetching {content_label}...")
            anime = scraper.fetch_playlist(
                anime, voice_id=selected_voice_id, player_id=selected_player_id
            )

            if anime.is_movie:
                print("Found movie file")
            else:
                print(f"Found {anime.total_episodes} episodes")

        if not anime.episodes:
            print("No episodes found!")
            sys.exit(1)

        # Step 7: Extract m3u8 URLs
        print("\nExtracting video URLs...")
        anime.episodes = extractor.extract_all_m3u8_urls(anime.episodes)

        # Count successful extractions
        successful_extractions = sum(1 for ep in anime.episodes if ep.m3u8_url)
        print(
            f"Successfully extracted {successful_extractions}/"
            f"{anime.total_episodes} URLs"
        )

        if successful_extractions == 0:
            print("Could not extract any video URLs. Exiting.")
            sys.exit(1)

        # Step 8: Create output directory
        output_dir = downloader.create_output_directory(anime, args.output)
        print(f"\nSaving to: {output_dir}")

        # Step 9: Download all episodes
        print(f"\nStarting download of {successful_extractions} episodes...\n")
        stats = downloader.download_all_episodes(anime, output_dir)

        # Print summary
        print("\n" + "=" * 50)
        print("Download Summary")
        print("=" * 50)
        print(f"Total episodes:      {stats['total']}")
        print(f"Successfully downloaded: {stats['success']}")
        print(f"Failed:              {stats['failed']}")
        print("=" * 50)

        if stats["failed"] > 0:
            print(
                "\nSome episodes failed to download. Check the logs above for details."
            )
            sys.exit(1)
        else:
            print("\nAll episodes downloaded successfully!")

    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("Fatal error occurred")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
