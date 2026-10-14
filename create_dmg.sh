#!/bin/bash
#
# Package dist/WhisperDoped.app into a distributable DMG.
#
# The DMG contains:
#   * WhisperDoped.app
#   * an Applications shortcut (drag-and-drop install)
#   * "Install & Open.command" — removes the download quarantine flag and
#     launches the app (works around Gatekeeper for an unsigned/ad-hoc app)
#   * a short README
#
# Usage: ./create_dmg.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="${VERSION:-0.2.0}"
APP_NAME="WhisperDoped"
ARCH="$(uname -m)"
DMG_NAME="${APP_NAME}-${VERSION}-macOS-${ARCH}.dmg"
APP="dist/${APP_NAME}.app"

if [ ! -d "$APP" ]; then
    echo "Error: $APP not found. Run ./build_app.sh first." >&2
    exit 1
fi

echo "==> Creating ${DMG_NAME}"
STAGE="/tmp/${APP_NAME}-dmg"
rm -rf "$STAGE"
mkdir -p "$STAGE"

# The app bundle itself
cp -R "$APP" "$STAGE/"

# Drag-to-install target
ln -s /Applications "$STAGE/Applications"

# First-launch helper: strip the quarantine attribute macOS adds on download,
# then open the installed app. Double-clickable from Finder.
cat > "$STAGE/Install & Open.command" <<'HELPER'
#!/bin/bash
# Copies Whisper Doped to /Applications (if needed), clears the "quarantine"
# flag that macOS puts on downloaded apps, and launches it.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/WhisperDoped.app"
DEST="/Applications/WhisperDoped.app"

echo "Whisper Doped installer"
echo "======================="

if [ ! -d "$DEST" ]; then
    echo "Copying to /Applications ..."
    rm -rf "$DEST"
    cp -R "$SRC" "$DEST" || {
        echo "!! Could not write to /Applications."
        echo "   Drag WhisperDoped.app onto the Applications shortcut instead,"
        echo "   then run:  xattr -dr com.apple.quarantine \"$DEST\""
        read -r -p "Press Return to close." _; exit 1;
    }
fi

echo "Clearing the download quarantine flag ..."
xattr -dr com.apple.quarantine "$DEST" 2>/dev/null || true

echo "Launching Whisper Doped ..."
open "$DEST"

echo ""
echo "Done. Whisper Doped is now in your menu bar (no Dock icon)."
echo ""
echo "Next steps:"
echo "  1. Grant Microphone + Accessibility (and Input Monitoring if asked)"
echo "     when macOS prompts."
echo "  2. Wait for the menu bar to say \"Model ready\" — the first launch"
echo "     downloads the speech model once (~1.6 GB), then it works offline."
echo "  3. Click into any text field, HOLD Right Option (Option key), speak,"
echo "     and release — your text is typed in where the cursor is."
sleep 2
HELPER
chmod +x "$STAGE/Install & Open.command"

cat > "$STAGE/README.txt" <<'README'
Whisper Doped — free, open-source, local dictation for macOS
============================================================

Whisper Doped is an independent, open-source project. It is NOT affiliated
with, endorsed by, or connected to Wispr Flow / Wispr AI, Inc. "Wispr Flow"
and related names are trademarks of their respective owners. This is a
clean-room, local-first reimplementation. Full project:
https://github.com/TotallyIndecisive/whisper-doped-v1

Install
-------
1. Double-click "Install & Open.command". It copies the app to /Applications,
   clears the download-quarantine flag and launches it.

   Prefer to do it by hand? Drag "WhisperDoped.app" onto the Applications
   shortcut in this window, then continue to step 2.

2. First launch of an unsigned app is blocked by macOS ("cannot be opened").
   Clear it with ONE of these (only needed once):

     a) Double-click "Install & Open.command" (easiest), or
     b) In Finder, right-click WhisperDoped.app -> Open -> Open, or
     c) In Terminal, run:
          xattr -dr com.apple.quarantine /Applications/WhisperDoped.app
        then open the app.

3. macOS will ask for Microphone and Accessibility permissions. Grant both —
   Accessibility is what lets Whisper Doped type text into other apps and
   listen for the global hotkey. Grant Input Monitoring too if asked.

4. On first launch the menu bar shows "Loading model…" and downloads the
   speech model once (~1.6 GB for the default). Wait for "Model ready".

Getting started
---------------
* Whisper Doped lives in the menu bar (no Dock icon). Look for the small
  status item: idle / recording / transcribing.
* Click into any text field, then HOLD Right Option (⌥), speak, and RELEASE.
  The cleaned-up text is typed in where your cursor is.  (push-to-talk)
* Or press Ctrl+Alt+Space to start, and again to stop.  (toggle)
* Tidy-up is automatic: fillers are removed ("um, so the the ..." ->
  "So the ..."), spoken punctuation works ("hello comma world period" ->
  "Hello, world."), and "scratch that" deletes the last sentence.
* Click the menu-bar item for History…, Dictionary… (names/jargon,
  replacements, snippets), Reveal data folder, Mode, and Quit.

Everything runs on your Mac. The only network use is the one-time model
download, after which it works fully offline.
README

# Build the compressed DMG
rm -f "dist/${DMG_NAME}"
hdiutil create \
    -volname "Whisper Doped" \
    -srcfolder "$STAGE" \
    -ov \
    -format UDZO \
    "dist/${DMG_NAME}"

rm -rf "$STAGE"

echo "==> DMG created: dist/${DMG_NAME} ($(du -h "dist/${DMG_NAME}" | cut -f1))"
