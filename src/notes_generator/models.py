from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional


@dataclass
class VideoInfo:
    video_id: str
    title: str
    description: str
    publish_date: Optional[datetime]
    author_name: Optional[str]


# A backend takes a fully-built prompt and returns the generated notes text.
# Any function/callable matching this shape can be passed to
# pipeline.generate_notes_for_video in place of gemini_client.generate_notes.
NotesBackend = Callable[[str], str]
