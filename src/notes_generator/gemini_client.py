from google import genai
from google.genai import errors as genai_errors
from .config import GEMINI_MODEL, get_gemini_api_keys


class AllKeysExhaustedError(RuntimeError):
    pass


def generate_notes(prompt_text):
    api_keys = get_gemini_api_keys()

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
