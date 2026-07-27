from dotenv import load_dotenv

from .file_utils import build_output_filename, save_text_file
from .gemini_client import generate_notes
from .prompt_utils import build_prompt, select_prompt
from .youtube_utils import get_transcript, get_video_info


def main():
    load_dotenv()

    # 1 Ask for YouTube URL
    url = input("Enter YouTube URL: ").strip()

    # 2 Get video info
    video_id, title, description, publish_date, author_name = get_video_info(url)

    # 3 Get transcript
    transcript = get_transcript(video_id)

    # 4 Ask category & load prompt
    prompt_text, prompt_inputs = select_prompt()

    # Prepare available data
    prompt_data = {
        "title": title,
        "description": description,
        "publish_date": publish_date,
        "author": author_name,
        "transcript": transcript
    }

    # 5 Build prompt dynamically
    full_prompt = build_prompt(prompt_text, prompt_inputs, prompt_data)

    # 6 Generate notes
    output_text = generate_notes(full_prompt)

    # 7 Save output with date + author
    output_file = build_output_filename(title, publish_date, author_name)
    save_text_file(output_file, output_text, folder="output")
    print(f"✅ Notes saved to {output_file}")


if __name__ == "__main__":
    main()
