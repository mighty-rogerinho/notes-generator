import os
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"
OUTPUT_DIR = "output"
GEMINI_MODEL = "gemini-3-flash-preview"


def get_youtube_api_key():
    return os.getenv("YOUTUBE_API_KEY")


def get_gemini_api_keys():
    return [
        os.getenv("GOOGLE_API_KEY_1"),
        os.getenv("GOOGLE_API_KEY_2"),
        os.getenv("GOOGLE_API_KEY_3"),
    ]
