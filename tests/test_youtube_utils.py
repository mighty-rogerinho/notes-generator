from unittest.mock import MagicMock, patch

from notes_generator.youtube_utils import get_transcript


def test_get_transcript_joins_snippet_text():
    snippet_1 = MagicMock(text="Hello")
    snippet_2 = MagicMock(text="world")
    fake_api = MagicMock()
    fake_api.fetch.return_value = [snippet_1, snippet_2]

    with patch("notes_generator.youtube_utils.YouTubeTranscriptApi", return_value=fake_api):
        result = get_transcript("some-video-id")

    assert result == "Hello\nworld"


def test_get_transcript_returns_empty_string_on_error():
    fake_api = MagicMock()
    fake_api.fetch.side_effect = Exception("transcripts disabled")

    with patch("notes_generator.youtube_utils.YouTubeTranscriptApi", return_value=fake_api):
        result = get_transcript("some-video-id")

    assert result == ""
