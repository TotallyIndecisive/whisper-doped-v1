# Building Whisper Doped macOS Distribution

## Quick Start

To build the .app and DMG:

```bash
# From repo root
cd /Users/smckenzie/Development/q4-2026/rea/whisper-doped

# Build .app bundle
./build_app.sh

# Create DMG installer
./create_dmg.sh
```

Outputs:
- `dist/WhisperDoped.app` - The macOS app bundle (menu bar app)
- `dist/WhisperDoped-0.2.0-macOS-arm64.dmg` - DMG installer for distribution

## Testing the App

After building:
```bash
# Run the built app directly
open dist/WhisperDoped.app
```

Note: On first launch, macOS may show "unidentified developer" warning. Right-click → Open to bypass, or sign/notarize for distribution.

## Code Signing (Optional, for cleaner distribution)

For GitHub Releases with no warnings, you'll need Apple Developer ID. If you have it:

```bash
# Ad-hoc sign (helps locally)
codesign --force --deep --sign - dist/WhisperDoped.app

# Verify
codesign -vvv dist/WhisperDoped.app
```

Full notarization requires `xcrun notarytool` with credentials - beyond scope for local builds.

## Publishing to GitHub

1. Create a new GitHub repo (public) - e.g., `whisper-doped` or keep name
2. Add remote if needed: `git remote add origin https://github.com/YOUR_USERNAME/whisper-doped.git`
3. Commit all changes: `git add -A && git commit -m "Add macOS app packaging"`
4. Push: `git push -u origin main`
5. Tag release: `git tag v0.2.0 && git push origin v0.2.0`
6. Create GitHub Release and attach `dist/WhisperDoped-0.2.0-macOS-arm64.dmg`

## Notes

- The app runs as LSUIElement (menu bar only, no dock icon) - this is correct for rumps.
- Models are downloaded on first run from Hugging Face (keeps DMG small).
- Architecture: Built for arm64 (Apple Silicon). For Intel Macs, rebuild on Intel or build universal with `--arch=universal2`.
