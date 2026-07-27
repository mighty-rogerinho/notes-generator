import threading
from google import genai
from .config import GEMINI_MODEL, get_gemini_api_keys
from .spinner_utils import spinner

def generate_notes(prompt_text):
    api_keys = get_gemini_api_keys()

    done_event = threading.Event()

    t = threading.Thread(target=spinner, args=(done_event, "Generating notes with Gemini AI"))
    t.start()

    try:
        last_exception = None

        for key_index, key in enumerate(api_keys):
            try:
                client = genai.Client(api_key=key)

                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt_text
                )

                return response.text

            except Exception as e:
                last_exception = e

                # Detect 429 / quota error
                if "429" in str(e) or "quota" in str(e).lower():
                    # Stop spinner, print rotation message, then restart
                    done_event.set()
                    t.join()
                    
                    print(f"API key #{key_index+1} exhausted, switching to next key...")

                    done_event = threading.Event()
                    t = threading.Thread(target=spinner, args=(done_event, "Generating notes with Gemini AI"))
                    t.start()
                    continue
                else:
                    raise e

        raise RuntimeError("All API keys exhausted.") from last_exception

    finally:
        done_event.set()
        t.join()