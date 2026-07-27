# notes-generator

Turns a YouTube video into structured Markdown notes: it pulls the video's metadata and transcript, feeds them into a category-specific prompt (documentary, news, academic lecture, ...), and asks Gemini to write up clean, structured notes.

## Prerequisites

- Python 3.12+
- A [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com) key (for fetching video title/description/publish date)
- One or more [Gemini API](https://aistudio.google.com/apikey) keys (free tier). The client rotates across up to three keys automatically when one hits its quota, since the Gemini free tier is rate-limited per key.

## Install

Clone the repo first:

```bash
git clone <this-repo>
cd notes-generator
```

Then create a virtual environment and install, using whichever tab matches your OS:

### Linux / WSL (Debian/Ubuntu)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

`python` isn't aliased to `python3` by default on Debian/Ubuntu — that's why `python3` is used explicitly above. If you'd rather not type `python3` everywhere, `sudo apt install python-is-python3` adds the alias system-wide.

### macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

macOS ships `python3` out of the box the same way Linux does; if you installed Python via Homebrew instead, the same commands apply.

### Windows (PowerShell / cmd)

```powershell
py -m venv venv
venv\Scripts\activate
pip install -e ".[dev]"
```

Windows's official installer provides the `py` launcher instead of a bare `python3`. If you're running this from Git Bash or WSL instead of PowerShell/cmd, follow the Linux instructions above.

---

Any of the above installs the package in editable mode and puts a `notes-generator` command on your `PATH` for the rest of this README (see `[project.scripts]` in `pyproject.toml`). You'll need to `source venv/bin/activate` (or `venv\Scripts\activate` on Windows) again in each new terminal session before running `notes-generator`.

## Configure

```bash
cp .env.example .env
```

Fill in `.env` with your keys:

```
YOUTUBE_API_KEY=...
GOOGLE_API_KEY_1=...
GOOGLE_API_KEY_2=...
GOOGLE_API_KEY_3=...
```

`GOOGLE_API_KEY_2`/`_3` are optional — leave them blank if you only have one Gemini key, though having a few from different Google accounts lets you get further before hitting the free-tier quota.

## Run

```bash
notes-generator
```

You'll be prompted for a YouTube URL, then asked to pick a note category from the templates in `src/notes_generator/prompts/`. The generated notes are saved as a `.md` file in `output/` (gitignored — this is where your personal generated notes accumulate, not tracked source).

## Add a new prompt template

Drop a new `.md` file into `src/notes_generator/prompts/`. The first line can optionally declare which pieces of video data the prompt wants, e.g.:

```
PROMPT_INPUTS: title, description, publish_date, transcript
```

Only fields listed here (and present in the video data) get appended to the prompt sent to Gemini. Everything else in the file is the prompt body.

## Run tests

```bash
pytest
```

Tests cover the pure logic (filename sanitization, prompt building/parsing) and the trickier bits of `gemini_client`/`youtube_utils` via mocking — nothing hits a real API or network.

## Project layout

```
src/notes_generator/
    cli.py             # entry point (installed as the `notes-generator` command) — interactive shell only
    pipeline.py          # generate_notes_for_video: the actual fetch -> build -> generate -> save pipeline
    config.py             # settings + env var access, all in one place
    models.py             # VideoInfo dataclass, NotesBackend type (the "prompt in, notes out" shape)
    youtube_utils.py    # video metadata + transcript fetching
    prompt_utils.py      # prompt template loading/selection
    gemini_client.py    # Gemini API call + key rotation on quota errors
    file_utils.py        # output filename/sanitization helpers
    spinner_utils.py     # terminal spinner while waiting on Gemini
    prompts/             # note-category prompt templates (.md)
tests/                   # pytest suite, no network calls
output/                  # generated notes (gitignored)
```

`cli.py` only handles interactive input; `pipeline.generate_notes_for_video(url, prompt_file)` has no `input()` calls at all, so it can be driven directly (scripts, tests, or a future non-interactive CLI) without going through the terminal prompts.
