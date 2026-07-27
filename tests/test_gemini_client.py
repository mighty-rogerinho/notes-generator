from unittest.mock import MagicMock, patch

import pytest
from google.genai import errors as genai_errors

from notes_generator import gemini_client
from notes_generator.gemini_client import AllKeysExhaustedError


@pytest.fixture(autouse=True)
def three_keys(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY_1", "key-1")
    monkeypatch.setenv("GOOGLE_API_KEY_2", "key-2")
    monkeypatch.setenv("GOOGLE_API_KEY_3", "key-3")


def _client_returning(text):
    client = MagicMock()
    client.models.generate_content.return_value = MagicMock(text=text)
    return client


def _quota_error():
    return genai_errors.ClientError(429, {"message": "quota exceeded", "status": "RESOURCE_EXHAUSTED"})


def _non_quota_client_error():
    return genai_errors.ClientError(400, {"message": "bad request", "status": "INVALID_ARGUMENT"})


def test_generate_notes_returns_text_from_first_key():
    with patch.object(gemini_client.genai, "Client", return_value=_client_returning("notes!")):
        result = gemini_client.generate_notes("some prompt")

    assert result == "notes!"


def test_generate_notes_rotates_to_next_key_on_quota_error():
    exhausted_client = MagicMock()
    exhausted_client.models.generate_content.side_effect = _quota_error()

    working_client = _client_returning("notes from second key")

    with patch.object(gemini_client.genai, "Client", side_effect=[exhausted_client, working_client]):
        result = gemini_client.generate_notes("some prompt")

    assert result == "notes from second key"


def test_generate_notes_does_not_rotate_on_non_quota_client_error():
    broken_client = MagicMock()
    broken_client.models.generate_content.side_effect = _non_quota_client_error()

    with patch.object(gemini_client.genai, "Client", return_value=broken_client):
        with pytest.raises(genai_errors.ClientError, match="bad request"):
            gemini_client.generate_notes("some prompt")


def test_generate_notes_raises_all_keys_exhausted_when_every_key_hits_quota():
    exhausted_client = MagicMock()
    exhausted_client.models.generate_content.side_effect = _quota_error()

    with patch.object(gemini_client.genai, "Client", return_value=exhausted_client):
        with pytest.raises(AllKeysExhaustedError, match="All API keys exhausted"):
            gemini_client.generate_notes("some prompt")
