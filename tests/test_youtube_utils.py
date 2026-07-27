from unittest.mock import MagicMock, patch

import pytest
from youtube_transcript_api import TranscriptsDisabled

from notes_generator.youtube_utils import (
    VideoNotFoundError,
    expand_playlist_urls,
    get_transcript,
)


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


def test_expand_playlist_urls_returns_single_video_unchanged():
    with patch("notes_generator.youtube_utils.Playlist") as mock_playlist_cls:
        result = expand_playlist_urls("https://youtu.be/dQw4w9WgXcQ")

    assert result == ["https://youtu.be/dQw4w9WgXcQ"]
    mock_playlist_cls.assert_not_called()


def test_expand_playlist_urls_returns_single_video_with_incidental_list_param_unchanged():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLxxxx&index=3"

    with patch("notes_generator.youtube_utils.Playlist") as mock_playlist_cls:
        result = expand_playlist_urls(url)

    assert result == [url]
    mock_playlist_cls.assert_not_called()


def test_expand_playlist_urls_expands_playlist_under_the_cap():
    fake_playlist = MagicMock()
    fake_playlist.video_urls = [f"https://youtu.be/vid{i}" for i in range(5)]

    with patch("notes_generator.youtube_utils.Playlist", return_value=fake_playlist):
        result = expand_playlist_urls("https://www.youtube.com/playlist?list=PLxxxx")

    assert result == fake_playlist.video_urls


def test_expand_playlist_urls_truncates_and_warns_over_the_cap(capsys):
    fake_playlist = MagicMock()
    fake_playlist.video_urls = [f"https://youtu.be/vid{i}" for i in range(150)]

    with patch("notes_generator.youtube_utils.Playlist", return_value=fake_playlist):
        result = expand_playlist_urls("https://www.youtube.com/playlist?list=PLxxxx")

    assert len(result) == 100
    assert result == fake_playlist.video_urls[:100]
    assert "150 videos" in capsys.readouterr().out


def test_expand_playlist_urls_raises_on_empty_playlist():
    fake_playlist = MagicMock()
    fake_playlist.video_urls = []

    with patch("notes_generator.youtube_utils.Playlist", return_value=fake_playlist):
        with pytest.raises(VideoNotFoundError, match="No videos found"):
            expand_playlist_urls("https://www.youtube.com/playlist?list=PLxxxx")


def test_expand_playlist_urls_raises_on_unresolvable_url():
    with patch("notes_generator.youtube_utils.Playlist", side_effect=KeyError("list")):
        with pytest.raises(VideoNotFoundError, match="Could not find a video or playlist"):
            expand_playlist_urls("https://www.youtube.com/")
