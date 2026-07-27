from notes_generator.prompt_utils import build_prompt, parse_prompt_file


def test_parse_prompt_file_extracts_prompt_inputs_header(tmp_path):
    prompt_file = tmp_path / "Test editor.md"
    prompt_file.write_text(
        "PROMPT_INPUTS: title, description, transcript\n"
        "You are a helpful editor.\n"
    )

    prompt_text, prompt_inputs = parse_prompt_file(prompt_file)

    assert prompt_inputs == ["title", "description", "transcript"]
    assert prompt_text == "You are a helpful editor.\n"


def test_parse_prompt_file_without_header_returns_empty_inputs(tmp_path):
    prompt_file = tmp_path / "No header.md"
    prompt_file.write_text("Just a plain prompt body.\n")

    prompt_text, prompt_inputs = parse_prompt_file(prompt_file)

    assert prompt_inputs == []
    assert prompt_text == "Just a plain prompt body.\n"


def test_build_prompt_numbers_sections_in_order():
    result = build_prompt(
        "Base prompt.",
        ["title", "description"],
        {"title": "My Video", "description": "A description"},
    )

    assert "1) Title: My Video" in result
    assert "2) Description: A description" in result
    assert result.startswith("Base prompt.")


def test_build_prompt_skips_fields_missing_from_data():
    result = build_prompt(
        "Base prompt.",
        ["title", "author", "transcript"],
        {"title": "My Video"},
    )

    assert "Title: My Video" in result
    assert "Author" not in result
    assert "Transcript" not in result


def test_build_prompt_formats_transcript_section_specially():
    result = build_prompt(
        "Base prompt.",
        ["transcript"],
        {"transcript": "hello world"},
    )

    assert "Transcript (raw speech transcription begins below):" in result
    assert "hello world" in result
    assert "End of transcript" in result
    # transcript section should not use the generic numbered-field format
    assert "1) Transcript" not in result
