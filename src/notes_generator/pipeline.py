from .config import OUTPUT_DIR
from .file_utils import build_output_filename, save_text_file
from .gemini_client import generate_notes
from .models import NotesBackend
from .prompt_utils import build_prompt, parse_prompt_file
from .youtube_utils import get_transcript, get_video_info


def generate_notes_for_video(url: str, prompt_file, backend: NotesBackend = generate_notes) -> str:
    """
    Fetch a video's metadata and transcript, build the prompt for the given
    prompt template file, generate notes via `backend`, and save the result.

    Contains no input() calls, so it can be driven by any caller (interactive
    CLI, future non-interactive CLI flags, batch scripts, tests) — just pass
    in a URL and a prompt file path.

    Returns the path the notes were saved to.
    """
    video_info = get_video_info(url)
    transcript = get_transcript(video_info.video_id)

    prompt_text, prompt_inputs = parse_prompt_file(prompt_file)

    prompt_data = {
        "title": video_info.title,
        "description": video_info.description,
        "publish_date": video_info.publish_date,
        "author": video_info.author_name,
        "transcript": transcript
    }

    full_prompt = build_prompt(prompt_text, prompt_inputs, prompt_data)

    output_text = backend(full_prompt)

    output_filename = build_output_filename(video_info.title, video_info.publish_date, video_info.author_name)
    return save_text_file(output_filename, output_text, folder=OUTPUT_DIR)
