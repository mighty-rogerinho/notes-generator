import pytest

from notes_generator.config import PROMPTS_DIR, SHARED_RULES_PATH
from notes_generator.prompt_utils import (
    PromptNotFoundError,
    build_prompt,
    find_prompt_file,
    list_prompt_files,
    parse_prompt_file,
)


def test_list_prompt_files_returns_only_md_files_sorted(tmp_path):
    (tmp_path / "News editor.md").write_text("news")
    (tmp_path / "Documentary editor.md").write_text("doc")
    (tmp_path / "notes.txt").write_text("not a prompt")

    result = list_prompt_files(tmp_path)

    assert result == ["Documentary editor.md", "News editor.md"]


def test_find_prompt_file_matches_case_insensitively(tmp_path):
    (tmp_path / "News editor.md").write_text("news")

    result = find_prompt_file("news EDITOR", tmp_path)

    assert result == tmp_path / "News editor.md"


def test_find_prompt_file_matches_with_or_without_md_suffix(tmp_path):
    (tmp_path / "News editor.md").write_text("news")

    assert find_prompt_file("News editor.md", tmp_path) == tmp_path / "News editor.md"
    assert find_prompt_file("News editor", tmp_path) == tmp_path / "News editor.md"


def test_find_prompt_file_raises_with_available_categories_on_no_match(tmp_path):
    (tmp_path / "News editor.md").write_text("news")
    (tmp_path / "Documentary editor.md").write_text("doc")

    with pytest.raises(PromptNotFoundError, match="Documentary editor, News editor"):
        find_prompt_file("Nonexistent category", tmp_path)


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


def test_parse_prompt_file_substitutes_shared_rules_placeholder(tmp_path):
    shared_rules_file = tmp_path / "common_rules.md"
    shared_rules_file.write_text("Shared hygiene rules go here.")

    prompt_file = tmp_path / "Test editor.md"
    prompt_file.write_text(
        "You are a test editor.\n\n{{SHARED_RULES}}\n\nStructure using: ...\n"
    )

    prompt_text, _ = parse_prompt_file(prompt_file, shared_rules_path=shared_rules_file)

    assert "{{SHARED_RULES}}" not in prompt_text
    assert "Shared hygiene rules go here." in prompt_text


def test_parse_prompt_file_without_placeholder_never_reads_shared_rules(tmp_path):
    prompt_file = tmp_path / "Test editor.md"
    prompt_file.write_text("A prompt with no shared-rules placeholder at all.\n")

    prompt_text, _ = parse_prompt_file(
        prompt_file, shared_rules_path=tmp_path / "does-not-exist.md"
    )

    assert prompt_text == "A prompt with no shared-rules placeholder at all.\n"


@pytest.mark.parametrize("filename", [
    "Documentary editor.md",
    "News editor.md",
    "Prof. Jiang courses academic editor.md",
])
def test_real_prompt_files_wire_up_shared_rules_correctly(filename):
    prompt_text, _ = parse_prompt_file(PROMPTS_DIR / filename, shared_rules_path=SHARED_RULES_PATH)

    assert "{{SHARED_RULES}}" not in prompt_text
    assert "Do NOT include:" in prompt_text
    assert "Markdown horizontal rules" in prompt_text


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
