"""No-op insertion backend (unsupported platforms, or --dry-run style use)."""

from __future__ import annotations

from .base import BaseInserter


class NullInserter(BaseInserter):
    name = "null"

    def insert(self, text: str) -> str:
        return "noop"

    def available(self) -> bool:
        return True
