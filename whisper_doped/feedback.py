"""Subtle audio feedback via the OS's built-in system sounds.

The original plays a short cue when dictation starts/stops. On macOS we use the
same system sound files through ``afplay``; on other platforms we stay silent
(no bundled assets, no hard dependency).
"""

from __future__ import annotations

import shutil
import subprocess
import threading

from .platform_info import is_macos

_SOUNDS = {
    "start": "Pop",
    "stop": "Bottle",
    "done": "Tink",
    "error": "Basso",
}

_DIR = "/System/Library/Sounds/{}.aiff"


def _play(name: str) -> None:
    if not is_macos():
        return
    sound = _SOUNDS.get(name)
    if not sound:
        return
    player = shutil.which("afplay")
    if not player:
        return
    try:
        subprocess.Popen(
            [player, _DIR.format(sound)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def play(name: str) -> None:
    """Fire-and-forget a named cue on a background thread."""
    threading.Thread(target=_play, args=(name,), daemon=True).start()
