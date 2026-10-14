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
echo "Done. Look for the microphone icon in your menu bar."
echo "Grant Accessibility + Microphone permission when macOS asks."
sleep 2
HELPER
chmod +x "$STAGE/Install & Open.command"

cat > "$STAGE/README.txt" <<'README'
Whisper Doped — local, private dictation for macOS
==================================================

Install
-------
1. Drag "WhisperDoped.app" onto the Applications shortcut in this window.
   (Or double-click "Install & Open.command" to do it automatically.)

2. First launch: because this app is not signed with an Apple Developer ID,
   macOS will warn that it "cannot be opened". Do ONE of these:

     a) Double-click "Install & Open.command" (easiest), or
     b) In Finder, right-click WhisperDoped.app -> Open -> Open, or
     c) In Terminal, run:
          xattr -dr com.apple.quarantine /Applications/WhisperDoped.app
        then open the app.

   You only need to do this once.

3. macOS will ask for Microphone and Accessibility permissions. Grant both —
   Accessibility is what lets Whisper Doped type text into other apps and
   listen for the global hotkey.

Use
---
* Hold Right Option and speak, release to transcribe. (Push-to-talk)
* Or press Ctrl+Alt+Space to start/stop. (Toggle)
* The recognised text is typed into whatever app has focus.

Everything runs on your Mac. The first dictation downloads the speech model
(once), then works offline.
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
