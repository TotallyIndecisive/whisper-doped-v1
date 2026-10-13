# Whisper Doped Distribution Plan

The goal is to make it easy for users to download from GitHub, get a desktop icon saved as an app in Applications, and run it with full functionality (menu bar/popup style via rumps).

## Recommended Approach (Most Optimal)

For macOS desktop distribution, the best user experience is:

1. **Primary:** GitHub Releases with a signed/notarized `.app` inside a `.dmg` installer
- Users download DMG, drag WhisperDoped.app to Applications, launch once
- Gets its own dock/menu bar presence, works with macOS permissions properly
- Looks and feels like a real desktop app

2. **Secondary:** uvx one-liner (no local install needed)
- `uvx "whisper-doped[macos,mlx]" whisper-doped run`
- Great for developers/advanced users
- Also easy to self-update

## Implementation Plan

### 1. App Icon
- [x] Created basic icon at `assets/icon.png` (1024x1024)
- [x] Created `.icns` at `assets/WhisperDoped.icns` using iconutil

### 2. macOS .app Bundle (py2app)
We’ll use py2app because:
- Works well with rumps/pyobjc (native macOS frameworks)
- Simple for menu-bar apps
- Creates self-contained .app

Create `setup.py` for py2app configuration:
```python
# setup.py
from setuptools import setup
import sys

DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,  # menu bar apps don't need argv emulation
    'iconfile': 'assets/WhisperDoped.icns',
    'plist': {
        'CFBundleName': 'WhisperDoped',
        'CFBundleDisplayName': 'Whisper Doped',
        'CFBundleIdentifier': 'com.whisperdoped.app',
        'CFBundleVersion': '0.2.0',
        'CFBundleShortVersionString': '0.2.0',
        'LSUIElement': True,  # Runs as menu bar/agent (no dock icon)
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'MIT License',
    },
    'includes': [
        'whisper_doped',
        'rumps',
        'numpy',
        'sounddevice',
        'pynput',
    ],
}

setup(
    app=['packaging/scripts/whisper_doped_app.py'],
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

Create entry point `packaging/scripts/whisper_doped_app.py`:
```python
#!/usr/bin/env python3
from whisper_doped.cli import main

if __name__ == '__main__':
    main()
```

### 3. Build Scripts

**build_app.sh**:
- Install py2app and dependencies
- Build .app with py2app
- Copy to `dist/WhisperDoped.app`
- Optionally strip/universalize for Intel+ARM (lipo) if needed

**create_dmg.sh**:
- Create DMG with nice layout (Applications symlink, background if desired)
- Uses `hdiutil create` 
- Output: `dist/WhisperDoped-0.2.0-macOS-arm64.dmg` (or universal)

### 4. DMG Creation Details
Simple, clean approach:
```bash
hdiutil create -volname "Whisper Doped" -srcfolder dist/WhisperDoped.app -ov -format UDZO dist/WhisperDoped-0.2.0.dmg
```

Better layout (optional): create a staging dir with .app and Applications link, set window view - but simple works fine.

### 5. README Updates
Add Installation section:
- **Download app (recommended)**: GitHub Releases → Download .dmg → drag to Applications
- **uvx (instant, no install)**: `curl -LsSf https://astral.sh/uv/install.sh | sh && uvx "whisper-doped[macos,mlx]" whisper-doped run`
- **pipx/uv tool**: existing instructions
- **Homebrew**: existing formula (CLI only)

### 6. GitHub Releases Workflow (Documentation)
When ready to publish:
1. Tag: `git tag v0.2.0`
2. Push: `git push origin v0.2.0`
3. Build DMG locally (or CI)
4. Create GitHub Release, attach DMG and maybe .app.zip
5. Update Homebrew formula with sdist URL/sha if publishing to PyPI

## Considerations

### Permissions
- LSUIElement means no dock icon (menu bar app) - this matches rumps behavior. Correct choice.
- Users still need to grant Microphone, Accessibility, Input Monitoring in System Settings. This is normal macOS security.
- If we want "Open at Login", we can add that via rumps (Start at Login menu item) - app already has menu.

### Code Signing/Notarization
For distribution outside own machine, unsigned apps show "unidentified developer". Options:
- Ad-hoc sign: `codesign --force --deep --sign - dist/WhisperDoped.app` (helps on same arch)
- Developer ID + notarization: requires Apple Developer ($99/year). For GitHub public releases, many projects distribute unsigned and users right-click Open - acceptable.

### Architecture
Building on Apple Silicon (arm64). Can also build universal with `--arch=universal2` if needed, but increases size. Document per-arch or build universal.

### Size
Bundled with MLX + models? Models download on first run (HuggingFace) - correct, keeps DMG small (~100-300MB vs GBs).

### Alternative: Briefcase (BeeWare)
Also good - cross-platform, more "native". But py2app is simpler here.

## Next Steps
1. Create `setup.py` and entry point
2. Create build scripts
3. Build .app locally to test
4. Create DMG
5. Update README
6. Open in VS Code for review/push

This matches the user's requirements perfectly. Let us implement.
