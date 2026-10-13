"""Platform detection and capability probing.

Everything that differs between macOS / Linux / Windows hangs off this module so
the rest of the code can ask questions instead of testing ``sys.platform``.
"""

from __future__ import annotations

import importlib.util
import platform
import shutil
import sys


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def is_windows() -> bool:
    return sys.platform.startswith("win")


def is_apple_silicon() -> bool:
    return is_macos() and platform.machine() == "arm64"


def arch() -> str:
    return platform.machine()


def has_command(name: str) -> bool:
    return shutil.which(name) is not None


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def is_wayland() -> bool:
    import os

    return bool(os.environ.get("WAYLAND_DISPLAY")) or os.environ.get("XDG_SESSION_TYPE") == "wayland"


def is_x11() -> bool:
    import os

    return bool(os.environ.get("DISPLAY"))
