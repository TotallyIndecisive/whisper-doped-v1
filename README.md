# Whisper Doped

A local, private dictation app for **macOS and Linux**, built as a clean-room
reimplementation of the **dictation half of Wispr Flow**
(`com.electron.wispr-flow`).

Hold a key, speak, release — the text is transcribed on your machine and typed
into whatever app has focus. No account, no sign-in, no cloud. Nothing you say
leaves the computer.

---

## What it does (and how it maps to the original)

The original app is an Electron shell + a Swift accessibility helper that streams
audio to hosted speech models. This project keeps the **architecture** and swaps
the server-side pieces for local ones:

| Wispr Flow (recovered) | Whisper Doped (local) |
| --- | --- |
| `renderer/dist/recorderWorklet.js` — AudioWorklet, 640‑frame PCM chunks | `audio.py` — `sounddevice` InputStream, 640‑frame blocks, 16 kHz mono |
| `TranscribeStream` gRPC (Baseten) → OpenAI fallback | `asr/` — pluggable local Whisper (see below) |
| `/llm/polish_text`, `/llm/formatting` | `polish.py` — deterministic local cleanup rules |
| Swift helper: AX direct-set, else clipboard paste | `insert/macos.py` — Accessibility direct-set, else clipboard paste |
| `org.nspasteboard.ConcealedType`, pasteboard restore | same, via `NSPasteboard` |
| Global keyboard service (push-to-talk / toggle) | `hotkey.py` — `pynput` global listener |
| Floating overlay panel | `ui/overlay_macos.py` — native `NSPanel` "pill" |
| Status-bar menu, `flow.sqlite` (history, dictionary) | `ui/macos.py`, `storage.py` (SQLite) |

**Intentionally omitted**: sign-in, accounts, sync, billing, Notetaker/meetings,
telemetry, auto-update, and the LLM "instruct/command" modes.

---

## Platform support

| | macOS (Apple Silicon) | macOS (Intel) | Linux (X11) | Linux (Wayland) |
| --- | --- | --- | --- | --- |
| Speech engine | **MLX** (GPU) or whisper.cpp | whisper.cpp / faster-whisper | whisper.cpp / faster-whisper | same |
| Microphone | ✅ | ✅ | ✅ | ✅ |
| Hotkey | ✅ | ✅ | ✅ | ⚠️ * |
| Text insertion | Accessibility + Cmd+V | same | `xdotool` | `wtype` / `ydotool` |
| Menu bar / tray | ✅ | ✅ | console mode | console mode |

\* Global hotkeys on Wayland need the compositor's permission (often via
`ydotool` or a systemd user service). The terminal still works everywhere.

### Speech-recognition backends

`asr/` ships three interchangeable backends; `auto` picks the first usable one:

| backend | install | needs | notes |
| --- | --- | --- | --- |
| `mlx` | `pip install mlx-whisper` | Apple Silicon | fastest on Macs (Metal GPU) |
| `whispercpp` | `pip install pywhispercpp` | CPU | whisper.cpp, very portable |
| `fasterwhisper` | `pip install faster-whisper` | CPU/CUDA | CTranslate2, good speed/accuracy |

`whisper-doped backends` shows which are usable on this machine.

---

## Install & run: quick start (macOS)

```bash
cd ~/Development/q4-2026/rea/whisper-doped
./run.sh                 # creates .venv, installs deps, starts the menu-bar app
```

- First launch downloads the Whisper model from Hugging Face (once).
- Verify the environment any time with `./run.sh selftest`.
- Run without a menu bar (keyboard only) with `./run.sh --console`.

### Install anywhere (pip / pipx / uv)

```bash
pipx install "whisper-doped[macos,mlx]"          # macOS with menu bar + MLX
pipx install "whisper-doped[whispercpp]"         # Linux / Intel: portable CPU

uv tool install "whisper-doped[whispercpp]"      # or via uv
whisper-doped run --console                       # terminal dictation
whisper-doped run                                 # menu bar (macOS)
```

### Homebrew (CLI)

The repository includes `packaging/homebrew/whisper-doped.rb` (see its header for
the two-step setup: publish to PyPI, then drop the formula into a
`homebrew-whisper-doped` tap repo):

```bash
brew tap YOU/whisper-doped
brew install whisper-doped
```

A future `Casks/whisper-doped.rb` (a signed, notarized `.app`) is the separate
"dedicated application" track and needs an Apple Developer account.

### macOS permissions (required)

The first time you dictate, macOS will ask. If it doesn't, open
**System Settings → Privacy & Security** and enable your terminal (or the Python
binary) under:

1. **Microphone** — to capture audio.
2. **Accessibility** — to type text into other apps and to read the focused field.
3. **Input Monitoring** — to receive the global hotkey.

Because you launch it from a terminal, macOS attributes these permissions to the
terminal app. If you want the permissions to belong to Whisper Doped itself, see
"Packaging as a real app" below.

### Linux prerequisites

```bash
# Wayland compositor (insertion + hotkey helpers)
sudo apt install wtype ydotool          # Debian/Ubuntu
sudo dnf install wtype ydotool          # Fedora
# X11 (insertion)
sudo apt install xdotool
```

---

## Using it

**Push-to-talk (default):** hold **Right Option (⌥)** while you speak, release to insert.

**Toggle mode:** press **Ctrl + Alt + Space** to start, press again to stop.
Switch modes from the menu-bar item "Mode: …".

Speak naturally. The result is cleaned up and typed where your cursor is:

- fillers removed — *"um, so the the meeting …"* → *"So the meeting …"*
- spoken punctuation — *"hello comma world period"* → *"Hello, world."*
- self-correction — *"at 5 actually 6pm"* → *"at 6pm"*
- *"scratch that"* deletes the sentence you just said

The menu bar shows the state (idle / recording / transcribing) and gives you:

- **History…** — your recent dictations (with source app + timing)
- **Dictionary…** — words to bias the recognizer, plus replacements & snippets
- **Reveal data folder** — opens the app's data directory

### Personal dictionary

Three kinds of entries (stored in `whisper_doped.sqlite`):

| kind | effect |
| --- | --- |
| `vocabulary` | passed to the model as context so it spells names/jargon your way |
| `replacement` | literal find→replace after transcription |
| `snippet` | like a replacement, good for signatures/boilerplate |

```bash
whisper-doped dict add "Kubernetes"                        # vocabulary
whisper-doped dict add "my signature" --kind snippet --replacement "Sam McKenzie
Staff Engineer"
whisper-doped dict list
```

### CLI

```bash
whisper-doped transcribe recording.wav --polish   # file -> text
whisper-doped insert "hello world" --delay 3      # type into the focused app
whisper-doped history -n 20
whisper-doped devices                             # list microphones
whisper-doped backends                            # usable speech engines
```

---

## Configuration

Stored in the platform data directory — `~/Library/Application Support/WhisperDoped`
on macOS, `$XDG_DATA_HOME/WhisperDoped` (`~/.local/share`) on Linux
(override with `WHISPER_DOPED_HOME`). Notable fields:

| field | default | meaning |
| --- | --- | --- |
| `asr_backend` | `auto` | `auto` / `mlx` / `whispercpp` / `fasterwhisper` |
| `model` | `mlx-community/whisper-large-v3-turbo` | MLX model repo |
| `whispercpp_model` | `small.en` | ggml name or `.bin` path |
| `fasterwhisper_model` | `small` | CTranslate2 model size |
| `language` | `null` | `null` auto-detects, or set e.g. `"en"` |
| `mode` | `push_to_talk` | or `toggle` |
| `push_to_talk_key` | `alt_r` | hold-to-talk key |
| `toggle_combo` | `ctrl+alt+space` | toggle shortcut |
| `polish` | `true` | run the cleanup pass |
| `insert_method` | `auto` | macOS: `auto` / `ax` / `clipboard`; Linux: `auto` / `type` / `clipboard` |
| `ui` | `auto` | `auto` / `menubar` / `console` |
| `restore_clipboard` | `true` | put your clipboard back after pasting |

Change a field in `config.json`, or:

```bash
whisper-doped run --backend whispercpp --model base.en
whisper-doped run --backend mlx --model mlx-community/whisper-small-mlx --console
whisper-doped transcribe x.m4a --backend fasterwhisper --polish
```

---

## Troubleshooting

| symptom | fix |
| --- | --- |
| Nothing happens on hotkey | Grant **Accessibility** + **Input Monitoring** (macOS), or check Wayland hotkey permissions (Linux). Restart the app. |
| "Microphone error" | Grant **Microphone**; check `whisper-doped devices`. |
| Text not appearing | Some apps block synthetic paste; set `insert_method` to `clipboard`. On Linux check `xdotool`/`wtype` is installed. |
| Clipboard wiped | `restore_clipboard` must be `true` (default). |
| Too slow | Switch to a smaller model (`small`, `tiny`) or a different backend. |
| Check everything | `whisper-doped selftest` |

---

## Packaging as a real macOS app (optional)

To get its own icon, permissions and "Open at login", bundle the virtualenv with
[`py2app`](https://py2app.readthedocs.io):

```bash
pip install "whisper-doped[macos,mlx]" py2app
# then build a .app that runs whisper_doped.cli:main (see py2app docs for setup.py)
```

For distribution without "unidentified developer" warnings you will also need a
Developer ID certificate + notarization (Apple Developer account).

---

## Project layout

```
whisper-doped/
├── run.sh                 launcher (creates venv, runs the app)
├── requirements.txt       full macOS dev install
├── pyproject.toml         package + extras (core installs on Linux)
├── packaging/homebrew/    Homebrew formula template
├── tests/
└── whisper_doped/
    ├── cli.py             command-line entry point
    ├── config.py          settings + data locations
    ├── platform_info.py   OS / capability detection
    ├── system.py          focused app, permissions, folder reveal
    ├── app.py             orchestrator (hotkey → record → transcribe → polish → insert)
    ├── audio.py           microphone capture + audio-file loading
    ├── polish.py          formatting / cleanup rules
    ├── hotkey.py          global push-to-talk / toggle
    ├── storage.py         SQLite history + dictionary
    ├── feedback.py        system-sound cues
    ├── asr/               pluggable speech recognition
    │   ├── factory.py     backend selection (auto/mlx/whispercpp/fasterwhisper)
    │   ├── mlx_backend.py / whispercpp_backend.py / fasterwhisper_backend.py
    ├── insert/            pluggable text insertion
    │   ├── factory.py     backend selection (macos/linux/null)
    │   ├── macos.py       AX direct-set + clipboard/Cmd+V
    │   ├── linux.py       wtype/xdotool type + clipboard fallback
    └── ui/                pluggable front ends
        ├── macos.py       menu bar (rumps)
        ├── console.py     terminal-only loop
        └── overlay_macos.py  floating state pill
```

## Privacy

Audio is processed entirely on-device. The only network access is the one-time
model download from Hugging Face. The optional cloud-polish pass is **off** by
default and only used if you add an OpenAI key and set `cloud_polish` to `true`.