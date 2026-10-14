# Whisper Doped

A free, open-source, local dictation app for **macOS and Linux**. Hold a key,
speak, release — the text is transcribed on your machine and typed into whatever
app has focus. No account, no sign-in, no cloud. Nothing you say leaves the
computer.

> **Not affiliated with Wispr Flow.**
> Whisper Doped is an independent, open-source project. It is **not affiliated
> with, endorsed by, sponsored by, or connected to Wispr Flow / Wispr AI, Inc.**
> "Wispr Flow", "Wispr" and any related names or logos belong to their respective
> owners and are used here only to describe the app it is compared to. See
> [License & disclaimer](#license--disclaimer).

---

## How Whisper Doped compares to Wispr Flow

From a user's point of view the two apps do the same everyday job: hold a key,
talk, and your words appear as text in whatever app you're using. The
differences are in how they run and what they ask of you.

| | Wispr Flow | Whisper Doped |
| --- | --- | --- |
| Price | Paid subscription (with a limited free tier) | **Free** |
| Sign-in | Requires an account | **No sign-in, no account, no subscription** |
| Where your voice goes | Processed in the cloud | **Stays on your Mac** — transcribed on-device |
| Offline use | Needs a connection | **Works offline** (after a one-time model download) |
| Open source | No | **Yes** — MIT licensed; read, fork or change it |
| Dictation limits | Word/time limits on the free tier | **Unlimited** |
| Platforms | Mac and Windows | **Any Mac** (Apple Silicon app; Intel via the terminal), plus Linux |
| Auto-formatting | Cloud AI formatting and voice commands | Local cleanup: fillers, punctuation, corrections, snippets |

**What's the same (the everyday experience)**

- Hold a key, speak, release — the text is typed where your cursor is.
- Use it in any app: email, chat, notes, documents, browsers, code editors.
- A menu-bar item shows the current state and holds your history and dictionary.

**Why people pick Whisper Doped**

- **Open source.** The whole app is public under the MIT License, so you can see
  exactly what it does, fork it, or change it. Nothing is hidden.
- **No sign-in.** There's no account, email, trial, or activation — install it
  and start dictating.
- **Private by design.** Your audio is transcribed on your own machine, so your
  voice never leaves your computer.
- **Runs on any Mac.** Apple Silicon Macs get the full menu-bar app; Intel Macs
  (and Linux) can run it from the terminal.
- **Free and unlimited.** No word counts, no time limits, no upsell.

> Wispr Flow is a separate, commercial product made by another company. The
> rows above describe its publicly facing, user-level features and may change
> over time; check its website for the current details. This comparison is about
> the user experience only.

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

## Install

There are two supported ways to get Whisper Doped running: the **desktop app
(DMG)** or **from the terminal**. Pick one — both give you the same menu-bar
dictation tool. When you're done installing, continue to
[Getting started](#getting-started-quick-tutorial).

### Path A — Desktop app (DMG, macOS Apple Silicon) — recommended

This installs a normal `WhisperDoped.app` you can launch from Applications.

**1. Download.** Go to the
[Releases page](https://github.com/TotallyIndecisive/whisper-doped-v1/releases)
and download `WhisperDoped-0.2.0-macOS-arm64.dmg`.

**2. Install.** Open the DMG, then **double-click `Install & Open.command`**. It
copies the app to `/Applications`, clears the download-quarantine flag (so macOS
lets it run) and launches it.

<details>
<summary>Prefer to drag it yourself? (manual steps)</summary>

1. Drag `WhisperDoped.app` onto the **Applications** shortcut in the DMG window.
2. The first launch of an unsigned app is blocked by macOS. Clear it with **one**
   of these:
   - right-click `WhisperDoped.app` → **Open** → **Open**, or
   - in Terminal:
     ```bash
     xattr -dr com.apple.quarantine /Applications/WhisperDoped.app
     ```
3. Launch it from Applications.

</details>

**3. Grant permissions.** macOS will prompt: allow **Microphone** and
**Accessibility**, and **Input Monitoring** if asked. See
[macOS permissions](#macos-permissions-required) if you miss the prompt.

**4. Wait for the model.** On first launch the menu bar shows *"Loading model…"*
and downloads the speech model once (~1.6 GB for the default). When it says
**"Model ready"** you're good to go.

Then jump to **[Getting started](#getting-started-quick-tutorial)**.

### Path B — Terminal (uvx, pipx/uv tool, or from source)

Works on macOS (Apple Silicon or Intel) and Linux. When you launch from a
terminal, macOS attributes Microphone/Accessibility permissions to your
**terminal app** rather than to Whisper Doped — that's expected.

**B1. uvx — run once without installing**

```bash
# 1. install uv (one command, no sudo)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. run Whisper Doped (Apple Silicon → MLX backend)
uvx "whisper-doped[macos,mlx] @ git+https://github.com/TotallyIndecisive/whisper-doped-v1" whisper-doped run
```

On an **Intel Mac** or **Linux**, swap the extras for the portable CPU backend:

```bash
uvx "whisper-doped[whispercpp] @ git+https://github.com/TotallyIndecisive/whisper-doped-v1" whisper-doped run
```

**B2. Install permanently (pipx or uv tool)**

```bash
# macOS (Apple Silicon): menu bar + MLX
pipx install "whisper-doped[macos,mlx] @ git+https://github.com/TotallyIndecisive/whisper-doped-v1"
# or
uv tool install "whisper-doped[macos,mlx] @ git+https://github.com/TotallyIndecisive/whisper-doped-v1"

# Intel Mac / Linux: portable CPU backend
pipx install "whisper-doped[whispercpp] @ git+https://github.com/TotallyIndecisive/whisper-doped-v1"

# run it
whisper-doped run              # menu bar (macOS) / console
whisper-doped run --console    # terminal only
```

**B3. From source (for development)**

```bash
git clone https://github.com/TotallyIndecisive/whisper-doped-v1.git
cd whisper-doped-v1
./run.sh            # creates .venv, installs deps, starts the menu-bar app
./run.sh selftest   # verify the environment at any time
./run.sh --console  # terminal-only mode
```

**Terminal notes**

- First launch downloads the speech model from Hugging Face (once).
- Grant **Microphone**, **Accessibility** and (if asked) **Input Monitoring** to
  your terminal in **System Settings → Privacy & Security**.
- Check the engine with `whisper-doped backends` and the mic with
  `whisper-doped devices`.

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

Whisper Doped needs three permissions. macOS usually prompts on first use; if it
doesn't, open **System Settings → Privacy & Security** and enable the relevant
entry:

1. **Microphone** — to capture audio.
2. **Accessibility** — to type text into other apps and to read the focused field.
3. **Input Monitoring** — to receive the global hotkey.

- **DMG install:** grant these to **Whisper Doped** (it appears by name).
- **Terminal install:** grant these to your **terminal app** (Terminal, iTerm,
  VS Code…), because that process launches the tool.

If you want the permissions to belong to Whisper Doped itself, use the DMG or
see "Packaging as a real macOS app" below.

### Linux prerequisites

```bash
# Wayland compositor (insertion + hotkey helpers)
sudo apt install wtype ydotool          # Debian/Ubuntu
sudo dnf install wtype ydotool          # Fedora
# X11 (insertion)
sudo apt install xdotool
```

---

## Getting started (quick tutorial)

You've installed Whisper Doped and granted permissions — here's your first
dictation.

**1. Find it in the menu bar.** Whisper Doped lives in the macOS menu bar (no
Dock icon). Look for a small status item whose title shows the current state:
`idle`, `recording`, or `transcribing`.

**2. Dictate something (push-to-talk).**

1. Click into any text field — Mail, Notes, a browser, a chat app.
2. **Hold the Right Option key (⌥)** and say:
   *"Hello world, this is my first dictation."*
3. **Release the key.** The status shows *transcribing…*, then the cleaned-up
   text is typed in at your cursor.

**3. Try toggle mode.** Press **Ctrl + Alt + Space** to start recording, speak,
then press it again to stop. Change the default from the menu-bar item
**Mode: …**.

**4. See the cleanup.** Whisper Doped tidies what it hears as it types:

- *"um, so the the meeting is at 5"* → **"So the meeting is at 5."**
- *"hello comma world period"* → **"Hello, world."**
- *"scratch that"* removes the sentence you just said.

**5. Explore the menu.** Click the menu-bar item:

- **History…** — your recent dictations (with the app they went to).
- **Dictionary…** — teach it names/jargon, and add replacements & snippets.
- **Reveal data folder** — open the folder holding your history + settings.
- **Mode / Quit** — switch hotkey style or exit.

**Hotkeys at a glance**

| action | key |
| --- | --- |
| dictate (push-to-talk, default) | hold **Right Option (⌥)**, release to insert |
| dictate (toggle mode) | **Ctrl + Alt + Space** to start / stop |
| quit | **Quit** from the menu-bar item |

That's it — everything runs on your machine, and the only network use is the
one-time model download. If something doesn't work, see
[Troubleshooting](#troubleshooting) or run `whisper-doped selftest`.

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

To build a distributable macOS app with its own icon:

```bash
cd /Users/smckenzie/Development/q4-2026/rea/whisper-doped
./build_app.sh   # Creates dist/WhisperDoped.app (~620 MB, MLX bundled)
./create_dmg.sh  # Creates dist/WhisperDoped-0.2.0-macOS-arm64.dmg
```

Requires an Apple Silicon Mac, Xcode Command Line Tools and Python 3.12. The
app is ad-hoc signed; a downloaded copy needs its quarantine flag cleared once
(the DMG ships an `Install & Open.command` helper that does this). See
[BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for details, and
[DISTRIBUTION_PLAN.md](DISTRIBUTION_PLAN.md) for the MLX/py2app gotchas handled
by the build script.

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

---

## License & disclaimer

Whisper Doped is **free and open-source software**, released under the
[MIT License](LICENSE). You're welcome to read, fork, modify and redistribute it.

It is an independent project and is **not affiliated with, endorsed by,
sponsored by, or connected to Wispr Flow / Wispr AI, Inc.** "Wispr Flow",
"Wispr" and any related names or logos are trademarks of their respective owners
and are used here only for comparison. Whisper Doped was written independently
and has no connection to that product.