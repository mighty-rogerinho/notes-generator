import requests
from datetime import datetime
from pytubefix import extract
from youtube_transcript_api import YouTubeTranscriptApi

from .config import get_youtube_api_key
from .models import VideoInfo

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"


class VideoNotFoundError(ValueError):
    pass


def get_video_info(url):
    """Return a VideoInfo for the given YouTube URL"""
    video_id = extract.video_id(url)

    response = requests.get(YOUTUBE_API_URL, params={
        "part": "snippet",
        "id": video_id,
        "key": get_youtube_api_key()
    })
    response.raise_for_status()

    items = response.json().get("items")
    if not items:
        raise VideoNotFoundError("No video found for this ID")

    snippet = items[0]["snippet"]

    print(f"Video: {snippet['title']}")
    print(f"Author: {snippet['channelTitle']}\n")

    return VideoInfo(
        video_id=video_id,
        title=snippet["title"],
        description=snippet["description"],
        publish_date=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
        author_name=snippet["channelTitle"]
    )

def get_transcript(video_id):
    """Return transcript text (all snippets joined). Raises if no transcript is available."""
    ytt_api = YouTubeTranscriptApi()
    fetched_transcript = ytt_api.fetch(video_id)
    return "\n".join([snippet.text for snippet in fetched_transcript])
