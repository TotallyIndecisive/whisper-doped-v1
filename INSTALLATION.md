# Installing Whisper Doped

## Option 1 — Download the app (recommended)

Gives you a `WhisperDoped.app` in Applications, like any other Mac app.

1. Go to the [Releases](https://github.com/TotallyIndecisive/whisper-doped-v1/releases)
   page and download `WhisperDoped-0.2.0-macOS-arm64.dmg`.
2. Open the DMG.
3. **Double-click `Install & Open.command`.** It copies the app to
   `/Applications`, clears the download-quarantine flag and launches it.

   *(Prefer dragging? Drag `WhisperDoped.app` onto the **Applications**
   shortcut, then — the first time only — right-click the app → **Open**, or
   run `xattr -dr com.apple.quarantine /Applications/WhisperDoped.app`.)*

The quarantine step is needed only once, because the app is not signed with a
paid Apple Developer ID. After that it opens normally.

> Requires an Apple Silicon Mac. For Intel Macs use Option 2 or 3 below with the
> `whispercpp` or `fasterwhisper` backend.

## Option 2 — uvx (no install, runs straight from GitHub)

```bash
# install uv once
curl -LsSf https://astral.sh/uv/install.sh | sh

# run (Apple Silicon / MLX)
uvx "whisper-doped[macos,mlx] @ git+https://github.com/TotallyIndecisive/whisper-doped-v1" whisper-doped run
```

## Option 3 — persistent install with pipx or uv

```bash
pipx install "whisper-doped[macos,mlx] @ git+https://github.com/TotallyIndecisive/whisper-doped-v1"
# or
uv tool install "whisper-doped[macos,mlx] @ git+https://github.com/TotallyIndecisive/whisper-doped-v1"

whisper-doped run
```

Intel Macs: swap `mlx` for `whispercpp` (e.g. `whisper-doped[macos,whispercpp]`).

## macOS permissions (required)

Grant these in **System Settings → Privacy & Security**:

1. **Microphone** — to record your voice.
2. **Accessibility** — to type recognised text into other apps and to receive
   the global hotkey.
3. **Input Monitoring** — may also be requested for the hotkey listener.

With the downloaded `.app`, the permissions attach to *Whisper Doped*. With
uvx/pipx they attach to your terminal or the `uv`/`python` process.

## Using it

* Hold **Right Option** and speak, release to transcribe (push-to-talk).
* Or press **Ctrl+Alt+Space** to start/stop (toggle).
* The text is typed into whatever app has focus.

Everything runs locally. The first dictation downloads the speech model once,
then it works offline.
