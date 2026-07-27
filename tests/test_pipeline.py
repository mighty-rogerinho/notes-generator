from datetime import datetime
from unittest.mock import MagicMock, patch

from notes_generator.models import VideoInfo
from notes_generator.pipeline import generate_notes_for_video


def fake_backend(prompt_text):
    return f"NOTES FOR: {prompt_text}"


def test_generate_notes_for_video_orchestrates_full_pipeline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    prompt_file = tmp_path / "Test editor.md"
    prompt_file.write_text(
        "PROMPT_INPUTS: title, transcript\n"
        "You are a test editor.\n"
    )

    video_info = VideoInfo(
        video_id="abc123",
        title="My Video",
        description="A description",
        publish_date=datetime(2024, 4, 10),
        author_name="Some Channel",
    )

    with patch("notes_generator.pipeline.get_video_info", return_value=video_info), \
         patch("notes_generator.pipeline.get_transcript", return_value="hello world transcript"):
        output_path = generate_notes_for_video(
            "https://youtu.be/abc123", prompt_file, backend=fake_backend
        )

    assert output_path == "output/2024-04-10 - My Video (Some Channel).md"

    saved_content = (tmp_path / output_path).read_text()
    assert saved_content.startswith("NOTES FOR:")
    assert "You are a test editor." in saved_content
    assert "hello world transcript" in saved_content


def test_generate_notes_for_video_skips_fields_missing_from_video_info(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    prompt_file = tmp_path / "Test editor.md"
    prompt_file.write_text(
        "PROMPT_INPUTS: title, author, transcript\n"
        "Base prompt.\n"
    )

    video_info = VideoInfo(
        video_id="abc123",
        title="My Video",
        description="",
        publish_date=None,
        author_name=None,
    )

    with patch("notes_generator.pipeline.get_video_info", return_value=video_info), \
         patch("notes_generator.pipeline.get_transcript", return_value=""):
        output_path = generate_notes_for_video(
            "https://youtu.be/abc123", prompt_file, backend=fake_backend
        )

    saved_content = (tmp_path / output_path).read_text()
    assert "Title: My Video" in saved_content
    assert "Author" not in saved_content


def test_generate_notes_for_video_uses_the_real_gemini_backend_by_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GOOGLE_API_KEY_1", "key-1")

    prompt_file = tmp_path / "Test editor.md"
    prompt_file.write_text("A plain prompt with no inputs.\n")

    video_info = VideoInfo(
        video_id="xyz", title="Another Video", description="", publish_date=None, author_name=None,
    )

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text="default backend notes")

    with patch("notes_generator.pipeline.get_video_info", return_value=video_info), \
         patch("notes_generator.pipeline.get_transcript", return_value=""), \
         patch("notes_generator.gemini_client.spinner", lambda done_event, msg: done_event.set()), \
         patch("notes_generator.gemini_client.genai.Client", return_value=fake_client):
        output_path = generate_notes_for_video("https://youtu.be/xyz", prompt_file)

    assert output_path == "output/Another Video.md"
    assert (tmp_path / output_path).read_text() == "default backend notes"
