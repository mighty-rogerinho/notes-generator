from unittest.mock import MagicMock, patch

import pytest

from notes_generator import gemini_client


@pytest.fixture(autouse=True)
def three_keys(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY_1", "key-1")
    monkeypatch.setenv("GOOGLE_API_KEY_2", "key-2")
    monkeypatch.setenv("GOOGLE_API_KEY_3", "key-3")


@pytest.fixture(autouse=True)
def no_spinner_thread(monkeypatch):
    # Spinner just needs to exit promptly in tests; run a no-op instead of the real loop.
    monkeypatch.setattr(gemini_client, "spinner", lambda done_event, msg: done_event.set())


def _client_returning(text):
    client = MagicMock()
    client.models.generate_content.return_value = MagicMock(text=text)
    return client


def test_generate_notes_returns_text_from_first_key():
    with patch.object(gemini_client.genai, "Client", return_value=_client_returning("notes!")):
        result = gemini_client.generate_notes("some prompt")

    assert result == "notes!"


def test_generate_notes_rotates_to_next_key_on_quota_error():
    exhausted_client = MagicMock()
    exhausted_client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED")

    working_client = _client_returning("notes from second key")

    with patch.object(gemini_client.genai, "Client", side_effect=[exhausted_client, working_client]):
        result = gemini_client.generate_notes("some prompt")

    assert result == "notes from second key"


def test_generate_notes_does_not_rotate_on_non_quota_error():
    broken_client = MagicMock()
    broken_client.models.generate_content.side_effect = ValueError("something unrelated broke")

    with patch.object(gemini_client.genai, "Client", return_value=broken_client):
        with pytest.raises(ValueError, match="something unrelated broke"):
            gemini_client.generate_notes("some prompt")


def test_generate_notes_raises_when_all_keys_exhausted():
    exhausted_client = MagicMock()
    exhausted_client.models.generate_content.side_effect = Exception("429 quota exceeded")

    with patch.object(gemini_client.genai, "Client", return_value=exhausted_client):
        with pytest.raises(RuntimeError, match="All API keys exhausted"):
            gemini_client.generate_notes("some prompt")
