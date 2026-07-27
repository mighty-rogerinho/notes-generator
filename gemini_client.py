import threading
import os
from google import genai
from spinner_utils import spinner

API_KEYS = [
    os.getenv("GOOGLE_API_KEY_1"),
    os.getenv("GOOGLE_API_KEY_2"),
    os.getenv("GOOGLE_API_KEY_3")
]

def generate_notes(prompt_text):
    done_event = threading.Event()
    
    t = threading.Thread(target=spinner, args=(done_event, "Generating notes with Gemini AI"))
    t.start()

    try:
        last_exception = None

        for key_index, key in enumerate(API_KEYS):
            try:
                client = genai.Client(api_key=key)

                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
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