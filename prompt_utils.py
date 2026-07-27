import os

def select_prompt(prompt_folder):
    """
    Dynamically loads all .md prompt files from a folder,
    asks the user to choose one, and returns:
    (prompt_text, filename, prompt_inputs)
    """

    # 1. Get all .md files
    prompt_files = sorted(
        f for f in os.listdir(prompt_folder)
        if f.lower().endswith(".md")
    )

    if not prompt_files:
        raise ValueError("No .md prompt files found in the prompts folder.")

    # 2. Display menu
    print("Select a category for this video:")
    for index, filename in enumerate(prompt_files, start=1):
        display_name = filename.replace(".md", "")
        print(f"{index}: {display_name}")

    # 3. Validate user input
    while True:
        choice = input("Enter number: ").strip()
        if choice.isdigit():
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(prompt_files):
                break
        print("Invalid choice. Please enter a valid number.")

    selected_file = prompt_files[choice_index]
    file_path = os.path.join(prompt_folder, selected_file)

    # 4. Read file and parse metadata
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    prompt_inputs = []
    if lines and lines[0].startswith("PROMPT_INPUTS:"):
        prompt_inputs = [x.strip() for x in lines[0].replace("PROMPT_INPUTS:", "").split(",")]
        prompt_text = "".join(lines[1:])  # remove metadata line
    else:
        prompt_text = "".join(lines)

    print(f"\n✅ Using prompt file: {selected_file}")

    return prompt_text, prompt_inputs

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