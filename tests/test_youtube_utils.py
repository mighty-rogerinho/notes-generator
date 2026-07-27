from unittest.mock import MagicMock, patch

import pytest
from youtube_transcript_api import TranscriptsDisabled

from notes_generator.youtube_utils import get_transcript


def test_get_transcript_joins_snippet_text():
    snippet_1 = MagicMock(text="Hello")
    snippet_2 = MagicMock(text="world")
    fake_api = MagicMock()
    fake_api.fetch.return_value = [snippet_1, snippet_2]

    with patch("notes_generator.youtube_utils.YouTubeTranscriptApi", return_value=fake_api):
        result = get_transcript("some-video-id")

    assert result == "Hello\nworld"


def test_get_transcript_propagates_error_instead_of_swallowing_it():
    fake_api = MagicMock()
    fake_api.fetch.side_effect = TranscriptsDisabled("some-video-id")

    with patch("notes_generator.youtube_utils.YouTubeTranscriptApi", return_value=fake_api):
        with pytest.raises(TranscriptsDisabled):
            get_transcript("some-video-id")
