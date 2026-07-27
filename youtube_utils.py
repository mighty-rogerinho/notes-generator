import os
import requests
from datetime import datetime
from pytubefix import extract
from youtube_transcript_api import YouTubeTranscriptApi

API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"

def get_video_info(url):
    """Return (video_id, title, description, publish_date, author)"""
    video_id = extract.video_id(url)

    response = requests.get(YOUTUBE_API_URL, params={
        "part": "snippet",
        "id": video_id,
        "key": API_KEY
    })
    response.raise_for_status()

    items = response.json().get("items")
    if not items:
        raise ValueError("No video found for this ID")

    snippet = items[0]["snippet"]

    print(f"Video: {snippet['title']}")
    print(f"Author: {snippet['channelTitle']}\n")

    return (
        video_id,
        snippet["title"],
        snippet["description"],
        datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
        snippet["channelTitle"]
    )

def get_transcript(video_id):
    """Return transcript text (all snippets joined)"""
    try:
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        return "\n".join([snippet.text for snippet in fetched_transcript])
    except Exception as e:
        print("⚠️ Error fetching transcript:", e)
        return ""