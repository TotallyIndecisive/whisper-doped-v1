#!/usr/bin/env python3
"""py2app configuration for the Whisper Doped menu-bar app.

Build with:

    ./build_app.sh

Notes
-----
* py2app refuses to build when the project metadata still carries
  ``install_requires`` (setuptools reads it from ``pyproject.toml``). The build
  script temporarily moves ``pyproject.toml`` aside while py2app runs.
* Packages with data files or native libraries (``_sounddevice_data`` with its
  bundled ``libportaudio.dylib``, ``mlx`` with its Metal kernels, ``pynput``'s
  platform backends, ``sqlite3``) must be listed in ``packages``/``includes`` so
  they are copied as real directories instead of being packed into
  ``python3xx.zip`` (where ``ctypes`` cannot ``dlopen`` them).
"""

from setuptools import setup
import sys

# modulegraph walks deeply nested ASTs while scanning large third-party
# packages (scipy/numba). The default limit trips a spurious RecursionError.
sys.setrecursionlimit(20000)

APP = ["packaging/scripts/whisper_doped_app.py"]

OPTIONS = {
    "argv_emulation": False,
    "iconfile": "assets/WhisperDoped.icns",
    "plist": {
        "CFBundleName": "WhisperDoped",
        "CFBundleDisplayName": "Whisper Doped",
        "CFBundleIdentifier": "com.whisperdoped.app",
        "CFBundleVersion": "0.2.0",
        "CFBundleShortVersionString": "0.2.0",
        "LSUIElement": True,  # menu-bar agent: no Dock icon, just the status item
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "12.0.0",
        "NSHumanReadableCopyright": "MIT License",
        "NSMicrophoneUsageDescription": (
            "Whisper Doped records your voice so it can transcribe it locally."
        ),
        "NSAccessibilityUsageDescription": (
            "Whisper Doped types the recognised text into the focused app and "
            "listens for your global dictation hotkey."
        ),
    },
    # Packages copied wholesale (real directories, not zipped). Anything with
    # data files or dlopen'ed native libraries belongs here.
    "packages": [
        "whisper_doped",
        "numpy",
        "sounddevice",
        "_sounddevice_data",  # ships libportaudio.dylib (loaded via ctypes)
        "pynput",             # ships the per-platform keyboard/mouse backends
        "rumps",
        "mlx_whisper",
        "scipy",              # mlx_whisper.timing uses scipy.signal
        "numba",              # mlx_whisper.timing uses numba.jit
        "llvmlite",           # numba's code generator
        "tiktoken",           # native tokeniser used by mlx_whisper
    ],
    # Modules that modulegraph may miss because they are imported lazily.
    "includes": [
        "sqlite3",
        "_sqlite3",
        "pynput.keyboard._darwin",
        "pynput.mouse._darwin",
        "Cocoa",
        "Quartz",
        "ApplicationServices",
        "AppKit",
        "Foundation",
    ],
    "excludes": [
        "matplotlib",
        "IPython",
        "jupyter",
        "notebook",
        "tkinter",
        "test",
        "torch",     # only referenced by mlx_whisper.torch_whisper (compat shim)
        "pandas",
        "PIL",       # Pillow drags in libtiff/liblzma; unused by the app and
        "Pillow",    # its stale ad-hoc signatures break bundle signing
        "_lzma",
        "lzma",
    ],
}

setup(
    name="WhisperDoped",
    app=APP,
    options={"py2app": OPTIONS},
)
