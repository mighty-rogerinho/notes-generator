from datetime import datetime

from notes_generator.file_utils import build_output_filename, sanitize_filename


def test_sanitize_filename_replaces_colon_and_removes_invalid_chars():
    result = sanitize_filename('Title: "Quoted" <Thing>? *|')
    assert ":" not in result
    assert '"' not in result
    assert "<" not in result and ">" not in result
    assert "?" not in result
    assert "*" not in result
    assert "|" not in result
    assert result.startswith("Title -")


def test_sanitize_filename_replaces_slashes_with_dash():
    assert sanitize_filename("A/B\\C") == "A-B-C"


def test_sanitize_filename_collapses_whitespace():
    assert sanitize_filename("Too   many    spaces") == "Too many spaces"


def test_sanitize_filename_truncates_long_titles():
    title = "x" * 150
    result = sanitize_filename(title, max_len=100)
    assert result == "x" * 100 + "..."


def test_sanitize_filename_leaves_short_titles_untouched():
    assert sanitize_filename("Short Title") == "Short Title"


def test_build_output_filename_with_date_and_author():
    date = datetime(2024, 4, 10)
    result = build_output_filename("My Video", publish_date=date, author_name="Some Channel")
    assert result == "2024-04-10 - My Video (Some Channel).md"


def test_build_output_filename_without_date():
    result = build_output_filename("My Video", publish_date=None, author_name="Some Channel")
    assert result == "My Video (Some Channel).md"


def test_build_output_filename_without_author():
    date = datetime(2024, 4, 10)
    result = build_output_filename("My Video", publish_date=date, author_name=None)
    assert result == "2024-04-10 - My Video.md"


def test_build_output_filename_without_date_or_author():
    result = build_output_filename("My Video")
    assert result == "My Video.md"
