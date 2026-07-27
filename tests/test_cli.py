from unittest.mock import patch

import pytest
import requests
from youtube_transcript_api import TranscriptsDisabled

from notes_generator.cli import (
    EmptyUrlsFileError,
    build_arg_parser,
    expand_urls,
    main,
    process_video,
    resolve_urls,
)
from notes_generator.gemini_client import AllKeysExhaustedError
from notes_generator.prompt_utils import PromptNotFoundError
from notes_generator.youtube_utils import VideoNotFoundError


@pytest.fixture(autouse=True)
def treat_every_url_as_a_single_video(monkeypatch):
    """Most tests in this file use short placeholder URLs (e.g. .../abc123)
    and aren't testing playlist expansion specifically - default
    expand_playlist_urls to a passthrough so they don't exercise real
    pytubefix URL parsing, which requires realistic 11-char video IDs.
    Tests that do want real expansion behavior override this locally via
    their own `with patch("notes_generator.cli.expand_playlist_urls", ...)`.
    """
    monkeypatch.setattr("notes_generator.cli.expand_playlist_urls", lambda url: [url])


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


def test_resolve_urls_empty_urls_file_raises_instead_of_silently_doing_nothing(tmp_path):
    urls_file = tmp_path / "videos.txt"
    urls_file.write_text("# just a comment, no actual URLs\n\n")

    args = build_arg_parser().parse_args(["--urls-file", str(urls_file)])

    with pytest.raises(EmptyUrlsFileError):
        resolve_urls(args)


# --- expand_urls --------------------------------------------------------------

def test_expand_urls_flattens_mixed_raw_entries():
    def fake_expand(url):
        if url == "https://youtu.be/playlist-link":
            return ["https://youtu.be/p1", "https://youtu.be/p2", "https://youtu.be/p3"]
        return [url]

    with patch("notes_generator.cli.expand_playlist_urls", side_effect=fake_expand):
        result = expand_urls(["https://youtu.be/single", "https://youtu.be/playlist-link"])

    assert result == [
        "https://youtu.be/single",
        "https://youtu.be/p1",
        "https://youtu.be/p2",
        "https://youtu.be/p3",
    ]


def test_expand_urls_reports_and_skips_a_failing_entry(capsys):
    def fake_expand(url):
        if url == "https://youtu.be/dead-playlist":
            raise VideoNotFoundError("No videos found in playlist")
        return [url]

    with patch("notes_generator.cli.expand_playlist_urls", side_effect=fake_expand):
        result = expand_urls(["https://youtu.be/good", "https://youtu.be/dead-playlist"])

    assert result == ["https://youtu.be/good"]
    assert "❌ https://youtu.be/dead-playlist:" in capsys.readouterr().out


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


def test_main_empty_urls_file_aborts_instead_of_silently_succeeding(tmp_path):
    urls_file = tmp_path / "videos.txt"
    urls_file.write_text("# no actual URLs here\n")

    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.generate_notes_for_video") as mock_generate:
        with pytest.raises(SystemExit) as exc_info:
            main(argv=["--urls-file", str(urls_file)])

    assert exc_info.value.code == 1
    mock_generate.assert_not_called()


def test_main_playlist_entry_expands_and_summary_reflects_expanded_total(tmp_path, capsys):
    urls_file = tmp_path / "videos.txt"
    urls_file.write_text("https://youtu.be/plain\nhttps://youtu.be/playlist-link\n")

    def fake_expand(url):
        if url == "https://youtu.be/playlist-link":
            return ["https://youtu.be/p1", "https://youtu.be/p2", "https://youtu.be/p3"]
        return [url]

    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.find_prompt_file", return_value="News editor.md"), \
         patch("notes_generator.cli.expand_playlist_urls", side_effect=fake_expand), \
         patch("notes_generator.cli.generate_notes_for_video", return_value="output/notes.md"):
        main(argv=["--urls-file", str(urls_file), "--category", "News editor"])

    assert "4/4 videos processed successfully." in capsys.readouterr().out


def test_main_all_entries_failing_to_expand_aborts_cleanly(capsys):
    with patch("notes_generator.cli.load_dotenv"), \
         patch("notes_generator.cli.find_prompt_file", return_value="News editor.md"), \
         patch("notes_generator.cli.expand_playlist_urls",
               side_effect=VideoNotFoundError("No videos found in playlist")), \
         patch("notes_generator.cli.generate_notes_for_video") as mock_generate:
        with pytest.raises(SystemExit) as exc_info:
            main(argv=["https://youtu.be/dead-playlist", "--category", "News editor"])

    assert exc_info.value.code == 1
    mock_generate.assert_not_called()
    assert "No videos to process." in capsys.readouterr().out
