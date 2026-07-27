from notes_generator.config import get_gemini_api_keys, get_youtube_api_key


def test_get_youtube_api_key_reads_env_var(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "yt-key-123")
    assert get_youtube_api_key() == "yt-key-123"


def test_get_gemini_api_keys_reads_all_three_env_vars(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY_1", "key-1")
    monkeypatch.setenv("GOOGLE_API_KEY_2", "key-2")
    monkeypatch.setenv("GOOGLE_API_KEY_3", "key-3")

    assert get_gemini_api_keys() == ["key-1", "key-2", "key-3"]
