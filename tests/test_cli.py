from unittest.mock import patch

import pytest
import requests
from youtube_transcript_api import TranscriptsDisabled

from notes_generator.cli import main
from notes_generator.gemini_client import AllKeysExhaustedError
from notes_generator.youtube_utils import VideoNotFoundError


def _run_main_with_pipeline_raising(exc, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "https://youtu.be/abc123")

    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.select_prompt", return_value="dummy_prompt.md"), \
         patch("notes_generator.cli.generate_notes_for_video", side_effect=exc):
        main()


@pytest.mark.parametrize("exc", [
    VideoNotFoundError("No video found for this ID"),
    TranscriptsDisabled("abc123"),
    requests.exceptions.HTTPError("403 Client Error"),
    AllKeysExhaustedError("All API keys exhausted."),
])
def test_main_prints_clean_message_and_exits_on_known_errors(exc, monkeypatch):
    with pytest.raises(SystemExit) as exc_info:
        _run_main_with_pipeline_raising(exc, monkeypatch)

    assert exc_info.value.code == 1


def test_main_prints_error_message_content(capsys, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "https://youtu.be/abc123")

    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.select_prompt", return_value="dummy_prompt.md"), \
         patch("notes_generator.cli.generate_notes_for_video", side_effect=VideoNotFoundError("No video found for this ID")):
        with pytest.raises(SystemExit):
            main()

    captured = capsys.readouterr()
    assert "❌" in captured.out
    assert "No video found for this ID" in captured.out


def test_main_lets_unknown_errors_propagate(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "https://youtu.be/abc123")

    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.select_prompt", return_value="dummy_prompt.md"), \
         patch("notes_generator.cli.generate_notes_for_video", side_effect=KeyError("unexpected bug")):
        with pytest.raises(KeyError):
            main()
