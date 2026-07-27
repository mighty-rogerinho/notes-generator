from dotenv import load_dotenv

from .pipeline import generate_notes_for_video
from .prompt_utils import select_prompt


def main():
    load_dotenv()

    url = input("Enter YouTube URL: ").strip()
    prompt_file = select_prompt()

    output_path = generate_notes_for_video(url, prompt_file)
    print(f"✅ Notes saved to {output_path}")


if __name__ == "__main__":
    main()
