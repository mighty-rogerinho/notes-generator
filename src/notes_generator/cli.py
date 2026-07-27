import sys

import requests
from dotenv import load_dotenv
from youtube_transcript_api import CouldNotRetrieveTranscript

from .gemini_client import AllKeysExhaustedError
from .pipeline import generate_notes_for_video
from .prompt_utils import select_prompt
from .youtube_utils import VideoNotFoundError

KNOWN_ERRORS = (
    VideoNotFoundError,
    CouldNotRetrieveTranscript,
    requests.exceptions.HTTPError,
    AllKeysExhaustedError,
)


def main():
    load_dotenv()

    url = input("Enter YouTube URL: ").strip()
    prompt_file = select_prompt()

    try:
        output_path = generate_notes_for_video(url, prompt_file)
    except KNOWN_ERRORS as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(f"✅ Notes saved to {output_path}")


if __name__ == "__main__":
    main()
