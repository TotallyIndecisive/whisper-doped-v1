# Building the Whisper Doped macOS app

## Requirements (one-time)

* Apple Silicon Mac (MLX is Apple-Silicon only)
* macOS 12 or newer
* Xcode Command Line Tools — `xcode-select --install`
* Python 3.12 — `brew install python@3.12` (the script falls back to `python3`)

## Build

```bash
cd /Users/smckenzie/Development/q4-2026/rea/whisper-doped

./build_app.sh     # -> dist/WhisperDoped.app  (~620 MB)
./create_dmg.sh    # -> dist/WhisperDoped-0.2.0-macOS-arm64.dmg  (~270 MB)
```

`build_app.sh` is self-contained: it creates `.venv`, installs the runtime and
build dependencies, runs py2app, fixes up the MLX runtime and ad-hoc signs the
bundle. Pass `--no-sign` to skip signing.

Why the bundle is large, and the non-obvious steps the script performs, are
documented in [DISTRIBUTION_PLAN.md](DISTRIBUTION_PLAN.md#non-obvious-gotchas-that-are-handled).

## Test the built app

```bash
# environment check
./dist/WhisperDoped.app/Contents/MacOS/WhisperDoped selftest

# transcribe a file (downloads the model on first use)
say -o /tmp/t.aiff "hello this is a test" && \
  afconvert -f WAVE -d LEI16@16000 -c 1 /tmp/t.aiff /tmp/t.wav && \
  ./dist/WhisperDoped.app/Contents/MacOS/WhisperDoped transcribe /tmp/t.wav \
    --backend mlx --model mlx-community/whisper-tiny

# launch the menu-bar app
open dist/WhisperDoped.app

# verify the signature
codesign --verify --deep --strict -v dist/WhisperDoped.app
```

## First launch on another Mac (Gatekeeper)

The app is ad-hoc signed, so a downloaded copy is quarantined. Clear it once by
double-clicking **`Install & Open.command`** inside the DMG, or:

```bash
xattr -dr com.apple.quarantine /Applications/WhisperDoped.app
```

A completely warning-free download needs an Apple Developer ID + notarization.

## Publish to GitHub

The repository is `TotallyIndecisive/whisper-doped-v1`.

```bash
git add -A
git commit -m "Working macOS .app + DMG build"
git push
git tag v0.2.0 && git push origin v0.2.0
```

Then create a GitHub Release and attach
`dist/WhisperDoped-0.2.0-macOS-arm64.dmg`.

## Notes

* The app runs as `LSUIElement` (menu-bar only, no Dock icon) — correct for rumps.
* Speech models download from Hugging Face on first use; they are not bundled.
* Built for arm64 (Apple Silicon). Intel Macs should use `uvx`/`pipx` with the
  `whispercpp` or `fasterwhisper` backend.
