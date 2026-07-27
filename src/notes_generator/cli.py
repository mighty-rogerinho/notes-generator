import argparse
import sys

import requests
from dotenv import load_dotenv
from youtube_transcript_api import CouldNotRetrieveTranscript

from .gemini_client import AllKeysExhaustedError
from .pipeline import generate_notes_for_video
from .prompt_utils import PromptNotFoundError, find_prompt_file, select_prompt
from .youtube_utils import VideoNotFoundError

# Bad --category / --urls-file: abort before touching any video.
SETUP_ERRORS = (PromptNotFoundError, FileNotFoundError)

# One video failing shouldn't sink the rest of a batch.
PER_VIDEO_ERRORS = (
    VideoNotFoundError,
    CouldNotRetrieveTranscript,
    requests.exceptions.HTTPError,
)

# Every Gemini key is dead - retrying the next video won't help either.
FATAL_ERRORS = (AllKeysExhaustedError,)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Generate Markdown notes from a YouTube video's transcript."
    )
    url_group = parser.add_mutually_exclusive_group()
    url_group.add_argument(
        "url", nargs="?", default=None,
        help="YouTube video URL (omit to be prompted, or use --urls-file for batch mode)"
    )
    url_group.add_argument(
        "--urls-file",
        help="Path to a text file of YouTube URLs, one per line (# comments and blank lines ignored)"
    )
    parser.add_argument(
        "--category",
        help="Prompt category name to use non-interactively (e.g. 'News editor'); omit to choose interactively"
    )
    return parser


def resolve_urls(args):
    if args.urls_file:
        with open(args.urls_file, encoding="utf-8") as f:
            return [
                line.strip() for line in f
                if line.strip() and not line.strip().startswith("#")
            ]

    if args.url:
        return [args.url]

    return [input("Enter YouTube URL: ").strip()]


def process_video(url, prompt_file):
    """Generate notes for one video. Returns True on success, False on a
    per-video failure (prints a clean message). Fatal errors propagate."""
    try:
        output_path = generate_notes_for_video(url, prompt_file)
    except PER_VIDEO_ERRORS as e:
        print(f"❌ {url}: {e}")
        return False

    print(f"✅ {url}: saved to {output_path}")
    return True


def main(argv=None):
    load_dotenv()

    args = build_arg_parser().parse_args(argv)

    try:
        urls = resolve_urls(args)
        prompt_file = find_prompt_file(args.category) if args.category else select_prompt()
    except SETUP_ERRORS as e:
        print(f"❌ {e}")
        sys.exit(1)

    try:
        results = [process_video(url, prompt_file) for url in urls]
    except FATAL_ERRORS as e:
        print(f"❌ {e}")
        sys.exit(1)

    if len(urls) > 1:
        print(f"\n{sum(results)}/{len(urls)} videos processed successfully.")

    if not all(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
