#!/bin/bash
#
# Build the Whisper Doped macOS .app bundle.
#
# Usage:
#   ./build_app.sh              # build dist/WhisperDoped.app
#   ./build_app.sh --no-sign    # skip the ad-hoc code signing step
#
# Requirements (one-time):
#   * Apple Silicon Mac (mlx-whisper is Apple-Silicon only)
#   * Xcode Command Line Tools:  xcode-select --install
#
# The script creates/repairs a local .venv, installs the runtime + build
# dependencies into it, then runs py2app from that interpreter so the bundle
# contains MLX, PortAudio and the other native pieces.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SIGN=1
for arg in "$@"; do
    case "$arg" in
        --no-sign) SIGN=0 ;;
    esac
done

PYTHON="${PYTHON:-$(command -v python3.12 || command -v python3)}"
VENV=".venv"

echo "==> Whisper Doped .app build"
echo "    python : $PYTHON ($("$PYTHON" -c 'import platform;print(platform.machine())'))"

# ------------------------------------------------------------------ 1. venv ---
if [ ! -d "$VENV" ]; then
    echo "==> Creating virtual environment"
    "$PYTHON" -m venv "$VENV"
fi

VPY="$VENV/bin/python"
"$VPY" -m pip install --upgrade pip wheel >/dev/null

echo "==> Installing runtime + build dependencies into $VENV"
"$VPY" -m pip install -e ".[macos,mlx]" >/dev/null

# py2app 0.28 needs the legacy `pkg_resources`, which setuptools >= 81 dropped,
# and the `imp` shim (via modulegraph) on Python 3.12+.
"$VPY" -m pip install "setuptools<81" "py2app" modulegraph macholib altgraph >/dev/null
"$VPY" -c "import pkg_resources, modulegraph" >/dev/null

# ------------------------------------------------------- 2. py2app build -----
echo "==> Cleaning previous build"
rm -rf build dist

# py2app 0.28 refuses to run if setuptools has populated install_requires from
# pyproject.toml. Hide it for the duration of the build.
HIDDEN=""
if [ -f pyproject.toml ]; then
    HIDDEN="pyproject.toml.buildtmp"
    mv pyproject.toml "$HIDDEN"
fi
restore_pyproject() {
    if [ -n "$HIDDEN" ] && [ -f "$HIDDEN" ]; then
        mv "$HIDDEN" pyproject.toml
    fi
}
trap restore_pyproject EXIT

echo "==> Running py2app"
"$VPY" setup.py py2app

restore_pyproject
trap - EXIT

if [ ! -d "dist/WhisperDoped.app" ]; then
    echo "!! Build failed: dist/WhisperDoped.app not found" >&2
    exit 1
fi

# ------------------------------------------------- 2b. bundle MLX properly -----
# `mlx` is a PEP 420 namespace package. py2app only copies the `core.so`
# extension and misses the rest of the package plus `mlx/lib/libmlx.dylib` and
# `mlx/lib/mlx.metallib`, without which `import mlx.core` fails at dlopen time.
# Copy the whole installed mlx tree next to core.so.
APP="dist/WhisperDoped.app"
SP="$("$VPY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
MLX_SRC="$SP/mlx"
CORE_SO="$(find "$APP/Contents/Resources" -path '*/mlx/core.so' 2>/dev/null | head -1)"
MLX_DEST="$(dirname "$CORE_SO")"
if [ -d "$MLX_SRC" ] && [ -n "$MLX_DEST" ] && [ -d "$MLX_DEST" ]; then
    echo "==> Bundling full MLX runtime (libmlx.dylib + mlx.metallib)"
    rsync -a --exclude '_code_signature' "$MLX_SRC/" "$MLX_DEST/"
    # Re-sign the freshly copied native libraries so the bundle stays valid.
    find "$MLX_DEST" -name "*.dylib" -exec codesign --force --sign - {} \; 2>/dev/null || true
else
    echo "!! Could not locate MLX to bundle (MLX backend may be unavailable)"
fi

# py2app byte-compiles the `mlx.core` extension loader into lib/python3xx.zip as a
# *regular* `mlx` package (with a stub __init__), which shadows the real
# namespace package we just copied. Strip `mlx/` from the zip so imports resolve
# to the complete tree next to core.so.
ZIP="$(find "$APP/Contents/Resources" -maxdepth 2 -name 'python3*.zip' | head -1)"
if [ -n "$ZIP" ]; then
    echo "==> Removing shadowing mlx stubs from $(basename "$ZIP")"
    "$VPY" - "$ZIP" <<'PYEOF'
import os, sys, zipfile
z = sys.argv[1]
tmp = z + ".new"
removed = 0
with zipfile.ZipFile(z) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        if item.filename == "mlx/" or item.filename.startswith("mlx/"):
            removed += 1
            continue
        zout.writestr(item, zin.read(item.filename))
os.replace(tmp, z)
print(f"    removed {removed} mlx entries")
PYEOF
fi

# --------------------------------------------------------------- 3. sign -----
if [ "$SIGN" -eq 1 ]; then
    echo "==> Ad-hoc signing (so Gatekeeper shows a friendlier message)"
    xattr -cr "$APP" 2>/dev/null || true
    if ! codesign --force --deep --sign - "$APP" 2>/tmp/wd_codesign.err; then
        echo "   !! ad-hoc signing failed:"; sed 's/^/      /' /tmp/wd_codesign.err
        echo "      (the app still runs locally; run 'codesign' manually if needed)"
    fi
fi

echo ""
echo "==> Build complete: $APP ($(du -sh "$APP" | cut -f1))"
echo "    Next: ./create_dmg.sh"
