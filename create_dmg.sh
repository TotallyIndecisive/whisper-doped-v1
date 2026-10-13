#!/bin/bash
set -e

# Get script directory and repo root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$SCRIPT_DIR"

cd "$REPO_ROOT"

VERSION="0.2.0"
APP_NAME="WhisperDoped"
DMG_NAME="${APP_NAME}-${VERSION}-macOS-arm64.dmg"

if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo "Error: dist/${APP_NAME}.app not found. Run ./build_app.sh first."
    exit 1
fi

echo "Creating DMG: ${DMG_NAME}..."

# Create a temporary directory for DMG contents
DMG_DIR="/tmp/${APP_NAME}-dmg"
rm -rf "${DMG_DIR}"
mkdir -p "${DMG_DIR}"

# Copy app to DMG staging
cp -R "dist/${APP_NAME}.app" "${DMG_DIR}/"

# Create Applications symlink
ln -s /Applications "${DMG_DIR}/Applications"

# Create DMG
hdiutil create \
  -volname "Whisper Doped" \
  -srcfolder "${DMG_DIR}" \
  -ov \
  -format UDZO \
  "dist/${DMG_NAME}"

rm -rf "${DMG_DIR}"

echo "✅ DMG created: dist/${DMG_NAME}"
ls -lh "dist/${DMG_NAME}"
