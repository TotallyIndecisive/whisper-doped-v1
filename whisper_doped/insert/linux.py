"""Linux insertion backend.

Prefers typing the text directly (no clipboard touched):

  * Wayland : ``wtype``
  * X11     : ``xdotool``

Falls back to writing the clipboard (``wl-copy`` / ``xclip`` / ``xsel``) and
sending Ctrl+V. The tools themselves are system packages -- we only call them:

    Debian/Ubuntu : sudo apt install wtype      # Wayland
                    sudo apt install xdotool     # X11
    Fedora        : sudo dnf install wtype xdotool
    Arch          : sudo pacman -S wtype xdotool
"""

from __future__ import annotations

import shutil
import subprocess
import time

from .base import BaseInserter


def _which(*names: str) -> str | None:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


class LinuxInserter(BaseInserter):
    name = "linux"

    def available(self) -> bool:
        return bool(_which("wtype", "xdotool", "ydotool"))

    # ------------------------------------------------------------------ helpers
    def _type_direct(self, text: str) -> bool:
        if _which("wtype"):
            return self._run(["wtype", "--", text])
        if _which("xdotool"):
            return self._run(["xdotool", "type", "--clearmodifiers", "--delay", "1", "--", text])
        return False

    def _send_paste(self) -> bool:
        if _which("wtype"):
            return self._run(["wtype", "-M", "ctrl", "-P", "v", "-p", "v", "-m", "ctrl"])
        if _which("xdotool"):
            return self._run(["xdotool", "key", "--clearmodifiers", "ctrl+v"])
        if _which("ydotool"):
            return self._run(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"])
        return False

    def _read_clipboard(self) -> bytes | None:
        if _which("wl-paste"):
            return self._capture(["wl-paste", "--no-newline"])
        if _which("xclip"):
            return self._capture(["xclip", "-selection", "clipboard", "-o"])
        if _which("xsel"):
            return self._capture(["xsel", "--clipboard", "--output"])
        return None

    def _write_clipboard(self, data: bytes) -> bool:
        if _which("wl-copy"):
            return self._run(["wl-copy"], input=data)
        if _which("xclip"):
            return self._run(["xclip", "-selection", "clipboard"], input=data)
        if _which("xsel"):
            return self._run(["xsel", "--clipboard", "--input"], input=data)
        return False

    @staticmethod
    def _run(cmd: list[str], input: bytes | None = None) -> bool:
        try:
            subprocess.run(cmd, input=input, check=True, timeout=10,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False

    @staticmethod
    def _capture(cmd: list[str]) -> bytes | None:
        try:
            return subprocess.run(cmd, check=True, timeout=5, capture_output=True).stdout
        except Exception:
            return None

    # ------------------------------------------------------------------ public
    def insert(self, text: str) -> str:
        if not text:
            return "noop"

        if self.method in ("auto", "type") and self._type_direct(text):
            return "type"

        saved = self._read_clipboard() if self.restore_clipboard else None
        if self._write_clipboard(text.encode("utf-8")):
            if self._send_paste():
                if saved is not None:
                    time.sleep(self.paste_delay)
                    self._write_clipboard(saved)
                return "clipboard"

        # last resort: try direct typing even if method said clipboard
        return "type" if self._type_direct(text) else "noop"
