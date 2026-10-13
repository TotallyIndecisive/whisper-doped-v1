# Installation Options for Whisper Doped

## Option 1: Download .app from GitHub (Recommended for most users)

This gives you a proper desktop app with an icon in Applications.

1. Go to [GitHub Releases](https://github.com/YOUR_USERNAME/whisper-doped/releases)
2. Download the latest `.dmg` file (e.g., `WhisperDoped-0.2.0-macOS-arm64.dmg`)
3. Open the DMG
4. Drag `WhisperDoped.app` to your Applications folder
5. Open `WhisperDoped.app` from Applications

**First launch:** If you see "cannot be opened because it is from an unidentified developer", right-click (or Ctrl+click) the app → Open → Open. This is normal for unsigned apps.

## Option 2: uvx (No install, just run)

Instant way to try it out without downloading the app.

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run Whisper Doped with MLX (Apple Silicon)
uvx "whisper-doped[macos,mlx]" whisper-doped run
```

You can also use a specific version:
```bash
uvx "whisper-doped[macos,mlx]@0.2.0" whisper-doped run
```

## Option 3: pipx / uv tool (Persistent install)

```bash
# pipx
pipx install "whisper-doped[macos,mlx]"

# or uv
uv tool install "whisper-doped[macos,mlx]"

# Run
whisper-doped run
```

## macOS Permissions (Required)

The first time you use Whisper Doped, macOS will ask for permissions. Grant them in System Settings → Privacy & Security:

1. **Microphone** - To record your voice
2. **Accessibility** - To type text into other apps
3. **Input Monitoring** - To receive global hotkeys

If using the downloaded .app, these permissions attach to WhisperDoped.app. If using uvx/pipx, they attach to the Python/uv process (or terminal). Both work fine.

## Notes

- **Architecture:** The DMG is built for Apple Silicon (arm64). If you're on Intel Mac, you may need to build from source or use Option 2/3 which work on both.
- **Privacy:** Everything runs locally. Models download once from Hugging Face.
- **Open at Login:** You can enable "Start at login" from the Whisper Doped menu bar item.
