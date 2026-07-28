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

### Termux (Android)

A plain `pip install -e ".[dev]"` fails here: pip has no prebuilt wheels for Android, so it tries to compile `cryptography` and `pydantic-core` from source (needs Rust) and `nodejs-wheel-binaries` (needed by `pytubefix` to run YouTube's signature-decryption JS; has no viable source build at all — it'd need a full Node.js build toolchain).

Run this instead — it's the whole workaround in one copy-pasteable block, so you can paste it as-is any time you need to set this up from scratch:

```bash
pkg install python-cryptography rust binutils nodejs
python3 -m venv --system-site-packages venv
source venv/bin/activate

# pytubefix expects a bundled Node binary at a specific path rather than
# checking PATH, so it won't find Termux's nodejs package on its own.
# This shim package points it there instead of letting pip try (and fail)
# to build nodejs-wheel-binaries from source.
mkdir -p /tmp/nodejs_wheel_shim/src/nodejs_wheel
touch /tmp/nodejs_wheel_shim/src/nodejs_wheel/__init__.py
cat > /tmp/nodejs_wheel_shim/pyproject.toml <<'EOF'
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "nodejs-wheel-binaries"
version = "22.20.0"
EOF
cat > /tmp/nodejs_wheel_shim/src/nodejs_wheel/executable.py <<'EOF'
import os, shutil
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(shutil.which("node"))))
EOF
pip install /tmp/nodejs_wheel_shim

pip install -e ".[dev]"
```

What each part does: `pkg install` pulls in Termux's own prebuilt `cryptography` and Node, plus a Rust toolchain (Termux's targets Android natively, unlike rustup's). The venv is created with `--system-site-packages` so it can see that prebuilt `cryptography`. The `cat > ... <<'EOF' ... EOF` blocks each write one file of the shim package — everything between the two `EOF` markers becomes that file's contents. `pip install /tmp/nodejs_wheel_shim` registers the shim so the final `pip install -e ".[dev]"` sees `nodejs-wheel-binaries` as already satisfied instead of trying (and failing) to build it. `pydantic-core` still compiles from source during that last step, which takes a minute or two — that's expected.

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

**Interactive** (no arguments — prompts for everything):

```bash
notes-generator
```

You'll be prompted for a YouTube URL, then asked to pick a note category from the templates in `src/notes_generator/prompts/`. The generated notes are saved as a `.md` file in `output/` (gitignored — this is where your personal generated notes accumulate, not tracked source).

**Single video, non-interactive:**

```bash
notes-generator "https://youtu.be/VIDEO_ID" --category "News editor"
```

`--category` matches a prompt template by its display name (case-insensitive, `.md` suffix optional — same names shown in the interactive menu). Omit it to still pick interactively even when the URL is given as an argument.

**Batch mode** — process a list of videos in one run:

```bash
cat > videos.txt <<'EOF'
https://youtu.be/VIDEO_ID_1
https://youtu.be/VIDEO_ID_2
# lines starting with # are ignored, as are blank lines
https://youtu.be/VIDEO_ID_3
EOF

notes-generator --urls-file videos.txt --category "News editor"
```

Every URL uses the same category. One video failing (no transcript available, bad URL, etc.) doesn't stop the rest of the batch — it's reported and the run continues; the process exits non-zero if anything failed so it's still scriptable. A summary line (`N/M videos processed successfully.`) prints at the end. The one exception is running out of usable Gemini API keys, which stops the batch immediately rather than burning through the remaining videos on a service that's already unusable.

**Playlists** are supported the same way, with no extra flag needed — a playlist link works anywhere a video URL does (the positional argument, or a line in `--urls-file`), and is auto-detected and expanded into its individual videos:

```bash
notes-generator "https://www.youtube.com/playlist?list=PLAYLIST_ID" --category "Documentary editor"
```

Capped at 100 videos per playlist — if a playlist has more, only the first 100 (in playlist order) are processed, with a warning printed. A `--urls-file` can freely mix individual video URLs and playlist links; each line is expanded independently.

## Add a new prompt template

Drop a new `.md` file into `src/notes_generator/prompts/`. The first line can optionally declare which pieces of video data the prompt wants, e.g.:

```
PROMPT_INPUTS: title, description, publish_date, transcript
```

Only fields listed here (and present in the video data) get appended to the prompt sent to Gemini. Everything else in the file is the prompt body.

Include the `{{SHARED_RULES}}` placeholder anywhere you want the common Markdown-hygiene rules injected (no meta-commentary, no horizontal rules, no emojis, etc.) — typically right before your "Structure using:" section, matching the three existing templates. Those shared rules live in one place, `src/notes_generator/prompts/_shared/common_rules.md`, so a rule that should apply to every category only needs editing once. That file isn't itself a selectable category — it's excluded automatically since prompt selection only looks at `.md` files directly inside `prompts/`, not its `_shared/` subfolder.

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
    file_utils.py        # output filename/sanitization + collision-safe saving
    prompts/             # note-category prompt templates (.md)
        _shared/          # common_rules.md - hygiene rules shared by every category via {{SHARED_RULES}}
tests/                   # pytest suite, no network calls
output/                  # generated notes (gitignored)
```

`cli.py` only handles interactive input; `pipeline.generate_notes_for_video(url, prompt_file)` has no `input()` calls at all, so it can be driven directly (scripts, tests, or a future non-interactive CLI) without going through the terminal prompts.
