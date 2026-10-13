"""macOS insertion backend.

Two-stage strategy recovered from the original bundle's Swift accessibility
helper:

  1. Direct Accessibility set - write ``kAXSelectedTextAttribute`` on the
     system-wide focused element. Fast, leaves the clipboard alone. Many apps
     do not support it and return an error, in which case we fall through.

  2. Clipboard paste - put the text on the pasteboard, synthesise Cmd+V, then
     restore the user's clipboard. The transient text is tagged with
     ``org.nspasteboard.ConcealedType`` (and ``TransientType``) so clipboard
     managers ignore it.
"""

from __future__ import annotations

import subprocess
import time
from typing import Any, Optional

from .base import BaseInserter

CONCEALED_TYPE = "org.nspasteboard.ConcealedType"
TRANSIENT_TYPE = "org.nspasteboard.TransientType"
_KEY_V = 9  # virtual keycode for "v"


class InsertionError(RuntimeError):
    pass


# --------------------------------------------------------------------------- loaders
def _load_appkit():
    from AppKit import NSPasteboard, NSPasteboardTypeString  # type: ignore
    from Foundation import NSData  # type: ignore

    return NSPasteboard, NSPasteboardTypeString, NSData


def _load_quartz():
    from Quartz import (  # type: ignore
        CGEventCreateKeyboardEvent,
        CGEventPost,
        CGEventSetFlags,
        kCGHIDEventTap,
        kCGEventFlagMaskCommand,
    )

    return CGEventCreateKeyboardEvent, CGEventPost, CGEventSetFlags, kCGHIDEventTap, kCGEventFlagMaskCommand


def _load_ax() -> Optional[dict[str, Any]]:
    try:
        from ApplicationServices import (  # type: ignore
            AXUIElementCreateSystemWide,
            AXUIElementCopyAttributeValue,
            AXUIElementSetAttributeValue,
            AXUIElementIsAttributeSettable,
            kAXFocusedUIElementAttribute,
            kAXSelectedTextAttribute,
        )

        return {
            "system_wide": AXUIElementCreateSystemWide,
            "copy_attr": AXUIElementCopyAttributeValue,
            "set_attr": AXUIElementSetAttributeValue,
            "is_settable": AXUIElementIsAttributeSettable,
            "focused": kAXFocusedUIElementAttribute,
            "selected_text": kAXSelectedTextAttribute,
        }
    except Exception:
        return None


# --------------------------------------------------------------------------- inserter
class MacInserter(BaseInserter):
    name = "macos"

    def __init__(self, method: str = "auto", restore_clipboard: bool = True, paste_delay: float = 0.18) -> None:
        super().__init__(method, restore_clipboard, paste_delay)
        self._ax = _load_ax()

    def available(self) -> bool:
        try:
            import AppKit  # noqa: F401

            return True
        except Exception:
            return False

    # ------------------------------------------------------------------ public
    def insert(self, text: str) -> str:
        if not text:
            return "noop"

        if self.method in ("auto", "ax") and self._ax is not None:
            if self._try_ax(text):
                return "ax"
            if self.method == "ax":
                self._paste_via_clipboard(text)
                return "clipboard"

        self._paste_via_clipboard(text)
        return "clipboard"

    # ------------------------------------------------------------- AX direct set
    def _try_ax(self, text: str) -> bool:
        if self._ax is None:
            return False
        try:
            system = self._ax["system_wide"]()
            err, focused = self._ax["copy_attr"](system, self._ax["focused"], None)
            if err != 0 or focused is None:
                return False
            settable, can = self._ax["is_settable"](focused, self._ax["selected_text"], None)
            if settable != 0 or not can:
                return False
            return self._ax["set_attr"](focused, self._ax["selected_text"], text) == 0
        except Exception:
            return False

    def selected_text(self) -> str:
        if self._ax is None:
            return ""
        try:
            system = self._ax["system_wide"]()
            err, focused = self._ax["copy_attr"](system, self._ax["focused"], None)
            if err != 0 or focused is None:
                return ""
            err, value = self._ax["copy_attr"](focused, self._ax["selected_text"], None)
            if err != 0 or value is None:
                return ""
            return str(value)
        except Exception:
            return ""

    # -------------------------------------------------------------- clipboard path
    def _paste_via_clipboard(self, text: str) -> None:
        saved: list[tuple[Any, Any]] = []
        pb = None
        try:
            NSPasteboard, NSPasteboardTypeString, NSData = _load_appkit()
            pb = NSPasteboard.generalPasteboard()
            saved = self._snapshot(pb)
            pb.clearContents()
            pb.declareTypes_owner_([NSPasteboardTypeString, CONCEALED_TYPE, TRANSIENT_TYPE], None)
            pb.setString_forType_(text, NSPasteboardTypeString)
            pb.setData_forType_(NSData.data(), CONCEALED_TYPE)
            pb.setData_forType_(NSData.data(), TRANSIENT_TYPE)
        except Exception:
            self._pbcopy(text)

        self._send_paste()

        if self.restore_clipboard and pb is not None:
            time.sleep(self.paste_delay)
            self._restore(pb, saved)

    @staticmethod
    def _snapshot(pb) -> list[tuple[Any, Any]]:
        items: list[tuple[Any, Any]] = []
        try:
            for t in (pb.types() or []):
                data = pb.dataForType_(t)
                if data is not None:
                    items.append((t, data))
        except Exception:
            pass
        return items

    @staticmethod
    def _restore(pb, saved: list[tuple[Any, Any]]) -> None:
        try:
            pb.clearContents()
            if saved:
                pb.declareTypes_owner_([t for t, _ in saved], None)
                for t, data in saved:
                    pb.setData_forType_(data, t)
        except Exception:
            pass

    @staticmethod
    def _pbcopy(text: str) -> None:
        try:
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=False, timeout=5)
        except Exception:
            pass

    def _send_paste(self) -> None:
        try:
            (
                CGEventCreateKeyboardEvent,
                CGEventPost,
                CGEventSetFlags,
                tap,
                cmd_mask,
            ) = _load_quartz()
            for down in (True, False):
                event = CGEventCreateKeyboardEvent(None, _KEY_V, down)
                CGEventSetFlags(event, cmd_mask)
                CGEventPost(tap, event)
                time.sleep(0.006)
            return
        except Exception:
            pass
        try:
            subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to keystroke "v" using command down'],
                check=False, timeout=5,
            )
        except Exception as exc:
            raise InsertionError(f"could not synthesise Cmd+V: {exc}") from exc
