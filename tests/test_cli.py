from unittest.mock import patch

import pytest
import requests
from youtube_transcript_api import TranscriptsDisabled

from notes_generator.cli import build_arg_parser, main, process_video, resolve_urls
from notes_generator.gemini_client import AllKeysExhaustedError
from notes_generator.prompt_utils import PromptNotFoundError
from notes_generator.youtube_utils import VideoNotFoundError


# --- resolve_urls -----------------------------------------------------------

def test_resolve_urls_from_single_url_arg():
    args = build_arg_parser().parse_args(["https://youtu.be/abc123"])
    assert resolve_urls(args) == ["https://youtu.be/abc123"]


def test_resolve_urls_from_urls_file_skips_blanks_and_comments(tmp_path):
    urls_file = tmp_path / "videos.txt"
    urls_file.write_text(
        "https://youtu.be/one\n"
        "\n"
        "# a comment\n"
        "https://youtu.be/two\n"
    )

    args = build_arg_parser().parse_args(["--urls-file", str(urls_file)])

    assert resolve_urls(args) == ["https://youtu.be/one", "https://youtu.be/two"]


def test_resolve_urls_falls_back_to_input_when_nothing_given(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "https://youtu.be/typed-in")

    args = build_arg_parser().parse_args([])

    assert resolve_urls(args) == ["https://youtu.be/typed-in"]


def test_resolve_urls_missing_urls_file_raises_file_not_found():
    args = build_arg_parser().parse_args(["--urls-file", "/no/such/file.txt"])

    with pytest.raises(FileNotFoundError):
        resolve_urls(args)


# --- process_video -----------------------------------------------------------

def test_process_video_returns_true_on_success(capsys):
    with patch("notes_generator.cli.generate_notes_for_video", return_value="output/notes.md"):
        result = process_video("https://youtu.be/abc123", "prompt.md")

    assert result is True
    assert "✅ https://youtu.be/abc123: saved to output/notes.md" in capsys.readouterr().out


@pytest.mark.parametrize("exc", [
    VideoNotFoundError("No video found for this ID"),
    TranscriptsDisabled("abc123"),
    requests.exceptions.HTTPError("403 Client Error"),
])
def test_process_video_returns_false_and_prints_clean_message_on_per_video_errors(exc, capsys):
    with patch("notes_generator.cli.generate_notes_for_video", side_effect=exc):
        result = process_video("https://youtu.be/abc123", "prompt.md")

    assert result is False
    captured = capsys.readouterr()
    assert "❌ https://youtu.be/abc123:" in captured.out


def test_process_video_lets_fatal_errors_propagate():
    with patch("notes_generator.cli.generate_notes_for_video",
               side_effect=AllKeysExhaustedError("All API keys exhausted.")):
        with pytest.raises(AllKeysExhaustedError):
            process_video("https://youtu.be/abc123", "prompt.md")


# --- main --------------------------------------------------------------------

def test_main_reproduces_interactive_single_video_flow(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "https://youtu.be/abc123")

    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.select_prompt", return_value="dummy_prompt.md") as mock_select, \
         patch("notes_generator.cli.generate_notes_for_video", return_value="output/notes.md"):
        main(argv=[])

    mock_select.assert_called_once()


def test_main_non_interactive_single_video(monkeypatch):
    input_called = []
    monkeypatch.setattr("builtins.input", lambda _: input_called.append(True))

    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.find_prompt_file", return_value="News editor.md") as mock_find, \
         patch("notes_generator.cli.generate_notes_for_video", return_value="output/notes.md"):
        main(argv=["https://youtu.be/abc123", "--category", "News editor"])

    mock_find.assert_called_once_with("News editor")
    assert input_called == []


def test_main_batch_mode_continues_past_per_video_errors(tmp_path, capsys):
    urls_file = tmp_path / "videos.txt"
    urls_file.write_text("https://youtu.be/good1\nhttps://youtu.be/bad\nhttps://youtu.be/good2\n")

    def fake_generate(url, prompt_file):
        if url == "https://youtu.be/bad":
            raise VideoNotFoundError("No video found for this ID")
        return f"output/{url.split('/')[-1]}.md"

    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.find_prompt_file", return_value="News editor.md"), \
         patch("notes_generator.cli.generate_notes_for_video", side_effect=fake_generate):
        with pytest.raises(SystemExit) as exc_info:
            main(argv=["--urls-file", str(urls_file), "--category", "News editor"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "✅ https://youtu.be/good1" in captured.out
    assert "❌ https://youtu.be/bad" in captured.out
    assert "✅ https://youtu.be/good2" in captured.out
    assert "2/3 videos processed successfully." in captured.out


def test_main_unknown_category_aborts_before_touching_any_video(monkeypatch):
    select_called = []
    monkeypatch.setattr("builtins.input", lambda _: select_called.append(True))

    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.find_prompt_file", side_effect=PromptNotFoundError("No prompt category matching 'nope'. Available: News editor")), \
         patch("notes_generator.cli.generate_notes_for_video") as mock_generate:
        with pytest.raises(SystemExit) as exc_info:
            main(argv=["https://youtu.be/abc123", "--category", "nope"])

    assert exc_info.value.code == 1
    mock_generate.assert_not_called()
    assert select_called == []


def test_main_fatal_error_stops_batch_before_remaining_urls(tmp_path):
    urls_file = tmp_path / "videos.txt"
    urls_file.write_text("https://youtu.be/one\nhttps://youtu.be/two\nhttps://youtu.be/three\n")

    attempted = []

    def fake_generate(url, prompt_file):
        attempted.append(url)
        if url == "https://youtu.be/two":
            raise AllKeysExhaustedError("All API keys exhausted.")
        return "output/notes.md"

    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.find_prompt_file", return_value="News editor.md"), \
         patch("notes_generator.cli.generate_notes_for_video", side_effect=fake_generate):
        with pytest.raises(SystemExit) as exc_info:
            main(argv=["--urls-file", str(urls_file), "--category", "News editor"])

    assert exc_info.value.code == 1
    assert attempted == ["https://youtu.be/one", "https://youtu.be/two"]


def test_main_missing_urls_file_aborts_cleanly():
    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.generate_notes_for_video") as mock_generate:
        with pytest.raises(SystemExit) as exc_info:
            main(argv=["--urls-file", "/no/such/file.txt"])

    assert exc_info.value.code == 1
    mock_generate.assert_not_called()
