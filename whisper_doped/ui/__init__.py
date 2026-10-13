"""UI selection: native macOS menu bar, or a terminal loop everywhere else."""

from __future__ import annotations

from ..config import Config
from ..platform_info import is_macos
from .overlay_base import NullOverlay


def create_overlay(config: Config):
    if config.show_overlay and is_macos():
        try:
            from .overlay_macos import MacOverlay

            return MacOverlay()
        except Exception:
            return NullOverlay()
    return NullOverlay()


def use_menubar(config: Config) -> bool:
    ui = (config.ui or "auto").lower()
    if ui == "console":
        return False
    if ui == "menubar":
        return is_macos()
    return is_macos() and config.show_menu_bar


def run(config: Config, dictapp, hotkeys, store) -> int:
    if not use_menubar(config):
        from .console import run_console

        return run_console(config, dictapp, hotkeys)
    from .macos import run_menubar

    return run_menubar(config, dictapp, hotkeys, store)
