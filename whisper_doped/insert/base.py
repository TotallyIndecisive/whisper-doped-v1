"""Common interface for insertion backends."""

from __future__ import annotations


class BaseInserter:
    name = "none"

    # The strategy used on macOS: "auto" | "ax" | "clipboard". Other backends
    # may interpret ``method`` differently (Linux: "auto" | "type" | "clipboard").
    def __init__(self, method: str = "auto", restore_clipboard: bool = True, paste_delay: float = 0.18) -> None:
        self.method = method
        self.restore_clipboard = restore_clipboard
        self.paste_delay = paste_delay

    def insert(self, text: str) -> str:
        raise NotImplementedError

    def selected_text(self) -> str:
        return ""

    def available(self) -> bool:
        return True
