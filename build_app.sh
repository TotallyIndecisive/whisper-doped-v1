#!/bin/bash
set -e

# Get script directory and repo root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$SCRIPT_DIR"

cd "$REPO_ROOT"

echo "Building Whisper Doped macOS .app..."

# Clean previous builds
rm -rf build dist

# Install py2app if not present
if ! pip show py2app >/dev/null 2>&1; then
    echo "Installing py2app..."
    pip install py2app
fi

# Build the app
echo "Running py2app..."
python setup.py py2app 2>&1 | tail -30

# Rename if needed
if [ -d "dist/WhisperDoped.app" ]; then
    echo "✅ Build successful: dist/WhisperDoped.app"
    ls -lh dist/
else
    echo "❌ Build failed"
    exit 1
fi

echo ""
echo "To create a DMG, run: ./create_dmg.sh"
