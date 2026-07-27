from datetime import datetime

from notes_generator.file_utils import build_output_filename, sanitize_filename, save_text_file


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


def test_save_text_file_writes_content_and_returns_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    returned_path = save_text_file("notes.md", "hello world", folder="output")

    assert returned_path == "output/notes.md"
    assert (tmp_path / "output" / "notes.md").read_text() == "hello world"


def test_save_text_file_without_folder(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    returned_path = save_text_file("notes.md", "hello world")

    assert returned_path == "notes.md"
    assert (tmp_path / "notes.md").read_text() == "hello world"


def test_save_text_file_does_not_overwrite_existing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    first_path = save_text_file("notes.md", "first version", folder="output")
    second_path = save_text_file("notes.md", "second version", folder="output")

    assert first_path == "output/notes.md"
    assert second_path == "output/notes (2).md"
    assert (tmp_path / "output" / "notes.md").read_text() == "first version"
    assert (tmp_path / "output" / "notes (2).md").read_text() == "second version"


def test_save_text_file_increments_past_multiple_collisions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    save_text_file("notes.md", "v1", folder="output")
    save_text_file("notes.md", "v2", folder="output")
    third_path = save_text_file("notes.md", "v3", folder="output")

    assert third_path == "output/notes (3).md"
    assert (tmp_path / "output" / "notes (3).md").read_text() == "v3"
