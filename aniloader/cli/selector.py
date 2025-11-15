"""Interactive selection UI for voices and players."""

import sys
import logging

from ..models import Voice, Player

logger = logging.getLogger(__name__)


class InteractiveSelector:
    """Interactive selector for voice and player options."""

    def select_voice(self, voices: list[Voice]) -> Voice:
        """Prompt user to select a voice option.

        Args:
            voices: List of available voices

        Returns:
            Selected Voice object

        Raises:
            SystemExit: If no voices available or user cancels
        """
        if not voices:
            print("No voice options found!")
            sys.exit(1)

        if len(voices) == 1:
            print(f"Using only available voice: {voices[0].name}")
            return voices[0]

        print("\nAvailable voice options:")
        for idx, voice in enumerate(voices, start=1):
            print(f"  {idx}. {voice.name}")

        while True:
            try:
                choice = input("\nSelect voice option (number): ").strip()
                choice_idx = int(choice) - 1

                if 0 <= choice_idx < len(voices):
                    selected = voices[choice_idx]
                    print(f"Selected: {selected.name}")
                    return selected
                else:
                    print(f"Invalid choice. Please enter 1-{len(voices)}")

            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\n\nCancelled by user")
                sys.exit(0)

    def select_player(self, players: list[Player]) -> Player:
        """Prompt user to select a player option.

        Args:
            players: List of available players

        Returns:
            Selected Player object

        Raises:
            SystemExit: If no players available or user cancels
        """
        if not players:
            print("No players found!")
            sys.exit(1)

        if len(players) == 1:
            print(f"Using only available player: {players[0].name}")
            return players[0]

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
                    return selected

                choice_idx = int(choice) - 1

                if 0 <= choice_idx < len(players):
                    selected = players[choice_idx]
                    print(f"Selected: {selected.name}")
                    return selected
                else:
                    print(f"Invalid choice. Please enter 1-{len(players)}")

            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\n\nCancelled by user")
                sys.exit(0)
