"""Insertion backend selection."""

from __future__ import annotations

from ..config import Config
from ..platform_info import is_linux, is_macos
from .base import BaseInserter


def resolve_backend(choice: str) -> str:
    choice = (choice or "auto").lower()
    if choice in ("auto", ""):
        if is_macos():
            return "macos"
        if is_linux():
            return "linux"
        return "null"
    return choice


def create_inserter(config: Config) -> BaseInserter:
    name = resolve_backend(config.insert_backend)
    kwargs = dict(
        method=config.insert_method,
        restore_clipboard=config.restore_clipboard,
        paste_delay=config.paste_delay,
    )
    if name == "macos":
        from .macos import MacInserter

        return MacInserter(**kwargs)
    if name == "linux":
        from .linux import LinuxInserter

        return LinuxInserter(**kwargs)
    from .null import NullInserter

    return NullInserter()
