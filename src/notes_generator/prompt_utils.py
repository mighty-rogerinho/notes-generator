import os
from pathlib import Path

from .config import PROMPTS_DIR, SHARED_RULES_PATH

SHARED_RULES_PLACEHOLDER = "{{SHARED_RULES}}"


def parse_prompt_file(file_path, shared_rules_path=SHARED_RULES_PATH):
    """
    Read a prompt .md file and split off its optional 'PROMPT_INPUTS:' header line.
    If the body contains the {{SHARED_RULES}} placeholder, substitute it with the
    contents of shared_rules_path (rules meant to apply to every prompt category).
    Returns (prompt_text, prompt_inputs).
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    prompt_inputs = []
    if lines and lines[0].startswith("PROMPT_INPUTS:"):
        prompt_inputs = [x.strip() for x in lines[0].replace("PROMPT_INPUTS:", "").split(",")]
        prompt_text = "".join(lines[1:])  # remove metadata line
    else:
        prompt_text = "".join(lines)

    if SHARED_RULES_PLACEHOLDER in prompt_text:
        with open(shared_rules_path, "r", encoding="utf-8") as f:
            shared_rules = f.read().strip()
        prompt_text = prompt_text.replace(SHARED_RULES_PLACEHOLDER, shared_rules)

    return prompt_text, prompt_inputs


class PromptNotFoundError(ValueError):
    pass


def list_prompt_files(prompt_folder=PROMPTS_DIR):
    """Return the sorted list of .md prompt filenames in a folder."""
    return sorted(
        f for f in os.listdir(prompt_folder)
        if f.lower().endswith(".md")
    )


def find_prompt_file(name, prompt_folder=PROMPTS_DIR):
    """
    Look up a prompt file by its display name (case-insensitive, .md suffix
    optional) for non-interactive category selection. Returns its path.
    """
    prompt_files = list_prompt_files(prompt_folder)
    normalized = name.strip().lower().removesuffix(".md")

    for filename in prompt_files:
        if filename.lower().removesuffix(".md") == normalized:
            return Path(prompt_folder) / filename

    available = ", ".join(f.removesuffix(".md") for f in prompt_files)
    raise PromptNotFoundError(
        f"No prompt category matching {name!r}. Available: {available}"
    )


def select_prompt(prompt_folder=PROMPTS_DIR):
    """
    Interactively ask the user to choose a prompt category from a folder
    of .md prompt files. Returns the path of the selected prompt file.
    """

    prompt_files = list_prompt_files(prompt_folder)

    if not prompt_files:
        raise ValueError("No .md prompt files found in the prompts folder.")

    # Display menu
    print("Select a category for this video:")
    for index, filename in enumerate(prompt_files, start=1):
        display_name = filename.replace(".md", "")
        print(f"{index}: {display_name}")

    # Validate user input
    while True:
        choice = input("Enter number: ").strip()
        if choice.isdigit():
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(prompt_files):
                break
        print("Invalid choice. Please enter a valid number.")

    selected_file = prompt_files[choice_index]
    file_path = Path(prompt_folder) / selected_file

    print(f"\n✅ Using prompt file: {selected_file}")

    return file_path

def build_prompt(prompt_text: str, prompt_inputs: list[str], prompt_data: dict) -> str:
    """
    Constructs the final prompt dynamically with automatic numbering.
    Fully future-proof: any field in prompt_inputs is included if present in prompt_data.
    Special formatting for 'transcript' section.
    """
    sections = []

    for i, field in enumerate(prompt_inputs, start=1):
        content = prompt_data.get(field, None)
        if content is None:
            continue  # skip fields not in prompt_data

        if field == "transcript":
            sections.append(
                "Transcript (raw speech transcription begins below):\n"
                "-----------------------------------------\n"
                f"{content}\n"
                "-----------------------------------------\n"
                "End of transcript"
            )
        else:
            # Capitalize the field name nicely
            label = field.replace("_", " ").capitalize()
            sections.append(f"{i}) {label}: {content}")

    return prompt_text + "\n\n" + "\n".join(sections)