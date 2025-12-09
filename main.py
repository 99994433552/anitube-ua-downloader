"""Refactored CLI interface for aniloader using SOLID principles."""

import sys
import argparse
import logging

from aniloader.factories.component_factory import ComponentFactory
from aniloader.exceptions import (
    AniloaderError,
    NoVoicesError,
    NoPlayersError,
    UserCancelledError,
)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Args:
        verbose: Enable debug logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Download anime episodes from anitube.in.ua"
    )

    parser.add_argument(
        "url",
        help="URL of the anime page on anitube.in.ua",
    )

    parser.add_argument(
        "--voice",
        type=int,
        help="Voice option index (1-based). If not provided, will ask interactively",
    )

    parser.add_argument(
        "--title",
        help="Custom title for output directory (overrides auto-detected title)",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=".",
        help="Output directory path (default: current directory)",
    )

    parser.add_argument(
        "--no-aria2c",
        action="store_true",
        help="Disable aria2c acceleration (use only yt-dlp)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_arguments()
    setup_logging(args.verbose)

    try:
        # Create orchestrator using factory
        orchestrator = ComponentFactory.create_orchestrator(
            use_aria2c=not args.no_aria2c
        )

        # Run download process
        stats = orchestrator.run(
            url=args.url,
            voice_index=args.voice,
            title=args.title,
            output_dir=args.output,
        )

        # Return exit code based on results
        if stats["failed"] > 0 and stats["successful"] == 0:
            return 1  # All failed
        return 0  # At least some succeeded

    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        return 130

    except UserCancelledError:
        print("\n\nCancelled by user")
        return 0

    except (NoVoicesError, NoPlayersError) as e:
        print(f"\nError: {e}")
        return 1

    except AniloaderError as e:
        logging.error(f"Aniloader error: {e}", exc_info=args.verbose)
        return 1

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
