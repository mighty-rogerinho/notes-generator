from google import genai
from google.genai import errors as genai_errors
from .config import GEMINI_MODEL, get_gemini_api_keys


class AllKeysExhaustedError(RuntimeError):
    pass


def generate_notes(prompt_text):
    api_keys = [key for key in get_gemini_api_keys() if key]

    if not api_keys:
        raise AllKeysExhaustedError(
            "No Gemini API keys are configured. Set GOOGLE_API_KEY_1 "
            "(and optionally _2/_3) in your .env file."
        )

    print("Generating notes with Gemini AI...")

    last_exception = None

    for key_index, key in enumerate(api_keys):
        try:
            client = genai.Client(api_key=key)

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt_text
            )

            return response.text

        except genai_errors.ClientError as e:
            last_exception = e

            if e.code == 429:
                print(f"API key #{key_index+1} exhausted, switching to next key...")
                continue
            else:
                raise

    raise AllKeysExhaustedError("All API keys exhausted.") from last_exception
