"""Overlay interface + the no-op implementation used off macOS."""

from __future__ import annotations


class NullOverlay:
    """A do-nothing overlay so the core never has to check for one."""

    def setup(self) -> bool:
        return False

    def show(self, text: str = "Listening\u2026") -> None:
        pass

    def update(self, text: str) -> None:
        pass

    def hide(self) -> None:
        pass
