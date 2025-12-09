"""Tests for selector module."""

import pytest
from unittest.mock import patch

from aniloader.cli.selector import InteractiveSelector
from aniloader.exceptions import NoVoicesError, NoPlayersError, UserCancelledError
from aniloader.models import Voice, Player


class TestInteractiveSelector:
    """Test InteractiveSelector class."""

    @pytest.fixture
    def selector(self):
        """Create selector instance."""
        return InteractiveSelector()

    def test_select_voice_single_voice(self, selector, capsys):
        """Test that single voice is auto-selected."""
        voices = [Voice(id="0_0", name="Test Voice")]
        result = selector.select_voice(voices)

        assert result == voices[0]
        captured = capsys.readouterr()
        assert "Using only available voice" in captured.out

    def test_select_voice_no_voices(self, selector):
        """Test that NoVoicesError is raised when no voices."""
        with pytest.raises(NoVoicesError):
            selector.select_voice([])

    @patch("builtins.input", return_value="1")
    def test_select_voice_user_choice(self, mock_input, selector):
        """Test user selecting first voice."""
        voices = [
            Voice(id="0_0", name="Voice 1"),
            Voice(id="0_1", name="Voice 2"),
        ]
        result = selector.select_voice(voices)

        assert result == voices[0]

    @patch("builtins.input", return_value="2")
    def test_select_voice_user_choice_second(self, mock_input, selector):
        """Test user selecting second voice."""
        voices = [
            Voice(id="0_0", name="Voice 1"),
            Voice(id="0_1", name="Voice 2"),
        ]
        result = selector.select_voice(voices)

        assert result == voices[1]

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_select_voice_keyboard_interrupt(self, mock_input, selector):
        """Test that KeyboardInterrupt raises UserCancelledError."""
        voices = [
            Voice(id="0_0", name="Voice 1"),
            Voice(id="0_1", name="Voice 2"),
        ]
        with pytest.raises(UserCancelledError):
            selector.select_voice(voices)

    @patch("builtins.input", side_effect=["invalid", "1"])
    def test_select_voice_invalid_then_valid(self, mock_input, selector, capsys):
        """Test invalid input followed by valid."""
        voices = [
            Voice(id="0_0", name="Voice 1"),
            Voice(id="0_1", name="Voice 2"),
        ]
        result = selector.select_voice(voices)

        assert result == voices[0]
        captured = capsys.readouterr()
        assert "Please enter a valid number" in captured.out

    @patch("builtins.input", side_effect=["5", "1"])
    def test_select_voice_out_of_range_then_valid(self, mock_input, selector, capsys):
        """Test out of range input followed by valid."""
        voices = [
            Voice(id="0_0", name="Voice 1"),
            Voice(id="0_1", name="Voice 2"),
        ]
        result = selector.select_voice(voices)

        assert result == voices[0]
        captured = capsys.readouterr()
        assert "Invalid choice" in captured.out

    # Player tests
    def test_select_player_single_player(self, selector, capsys):
        """Test that single player is auto-selected."""
        players = [Player(id="0_0_0", name="Test Player")]
        result = selector.select_player(players)

        assert result == players[0]
        captured = capsys.readouterr()
        assert "Using only available player" in captured.out

    def test_select_player_no_players(self, selector):
        """Test that NoPlayersError is raised when no players."""
        with pytest.raises(NoPlayersError):
            selector.select_player([])

    @patch("builtins.input", return_value="1")
    def test_select_player_user_choice(self, mock_input, selector):
        """Test user selecting first player."""
        players = [
            Player(id="0_0_0", name="Player 1"),
            Player(id="0_0_1", name="Player 2"),
        ]
        result = selector.select_player(players)

        assert result == players[0]

    @patch("builtins.input", return_value="")
    def test_select_player_empty_selects_first(self, mock_input, selector):
        """Test empty input selects first player."""
        players = [
            Player(id="0_0_0", name="Player 1"),
            Player(id="0_0_1", name="Player 2"),
        ]
        result = selector.select_player(players)

        assert result == players[0]

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_select_player_keyboard_interrupt(self, mock_input, selector):
        """Test that KeyboardInterrupt raises UserCancelledError."""
        players = [
            Player(id="0_0_0", name="Player 1"),
            Player(id="0_0_1", name="Player 2"),
        ]
        with pytest.raises(UserCancelledError):
            selector.select_player(players)

    @patch("builtins.input", side_effect=["invalid", "1"])
    def test_select_player_invalid_then_valid(self, mock_input, selector, capsys):
        """Test invalid input followed by valid for player selection."""
        players = [
            Player(id="0_0_0", name="Player 1"),
            Player(id="0_0_1", name="Player 2"),
        ]
        result = selector.select_player(players)

        assert result == players[0]
        captured = capsys.readouterr()
        assert "Please enter a valid number" in captured.out

    @patch("builtins.input", side_effect=["5", "1"])
    def test_select_player_out_of_range_then_valid(self, mock_input, selector, capsys):
        """Test out of range input followed by valid for player selection."""
        players = [
            Player(id="0_0_0", name="Player 1"),
            Player(id="0_0_1", name="Player 2"),
        ]
        result = selector.select_player(players)

        assert result == players[0]
        captured = capsys.readouterr()
        assert "Invalid choice" in captured.out
