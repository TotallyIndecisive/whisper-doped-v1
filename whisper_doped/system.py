"""Cross-platform system helpers: focused app, accessibility, folder reveal.

Everything here degrades to a safe no-op on platforms where it does not apply,
so callers never have to guard by OS themselves.
"""

from __future__ import annotations

import subprocess
from typing import Optional

from .platform_info import has_command, is_linux, is_macos


# --------------------------------------------------------------------- focused app
def frontmost_app_name() -> Optional[str]:
    """Name of the frontmost application (used for history). Best-effort."""
    if is_macos():
        try:
            from AppKit import NSWorkspace  # type: ignore

            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            return (str(app.localizedName()) or None) if app is not None else None
        except Exception:
            return None
    if is_linux():
        if has_command("xdotool"):
            try:
                out = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True, text=True, timeout=2,
                )
                return out.stdout.strip() or None
            except Exception:
                return None
    return None


# --------------------------------------------------------------------- accessibility
def accessibility_trusted() -> bool:
    """True when this process may drive Accessibility / event taps (macOS only)."""
    if not is_macos():
        return True
    try:
        from ApplicationServices import AXIsProcessTrusted  # type: ignore

        return bool(AXIsProcessTrusted())
    except Exception:
        try:
            from Quartz import AXIsProcessTrusted  # type: ignore

            return bool(AXIsProcessTrusted())
        except Exception:
            return False


def request_accessibility_prompt() -> bool:
    """Ask macOS to show the 'grant Accessibility' dialog.

    Also adds the app to the Accessibility list, so the user only has to flip
    the toggle. No-op elsewhere.
    """
    if not is_macos():
        return True
    try:
        from ApplicationServices import (  # type: ignore
            AXIsProcessTrustedWithOptions,
            kAXTrustedCheckOptionPrompt,
        )

        return bool(AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True}))
    except Exception:
        return accessibility_trusted()


# --------------------------------------------------------------------- misc
def open_folder(path: str) -> None:
    if is_macos():
        subprocess.Popen(["open", str(path)])
    elif is_linux():
        subprocess.Popen(["xdg-open", str(path)])
    else:  # pragma: no cover
        pass
