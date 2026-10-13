"""macOS menu-bar front end (rumps) plus the app launcher."""

from __future__ import annotations

import threading
import time

import rumps  # type: ignore

from ..config import Config, data_dir
from ..storage import Store, format_terms
from ..system import accessibility_trusted, open_folder


class MenuBarApp(rumps.App):
    def __init__(self, dictapp, config: Config, store: Store, hotkeys=None, log=print) -> None:
        super().__init__("Whisper Doped", quit_button=None)
        self.dictapp = dictapp
        self.config = config
        self.store = store
        self.hotkeys = hotkeys
        self.log = log

        self.status_item = rumps.MenuItem("Idle")
        self.mode_item = rumps.MenuItem(self._mode_label(), callback=self._toggle_mode)
        self.menu = [
            self.status_item,
            None,
            self.mode_item,
            rumps.MenuItem("Dictate now / stop", callback=lambda _s: self.dictapp.toggle()),
            None,
            rumps.MenuItem("History\u2026", callback=self._show_history),
            rumps.MenuItem("Dictionary\u2026", callback=self._show_dictionary),
            rumps.MenuItem("Reveal data folder", callback=self._reveal),
            None,
            rumps.MenuItem("About / permissions", callback=self._about),
            rumps.MenuItem("Quit", callback=self._quit),
        ]

    # ------------------------------------------------------------------ helpers
    def set_state(self, state: str) -> None:
        labels = {"idle": "Idle", "recording": "Recording\u2026", "transcribing": "Transcribing\u2026"}
        try:
            self.status_item.title = labels.get(state, state)
            if state == "recording":
                self.title = "\u23fa Rec"
            elif state == "transcribing":
                self.title = "\u22ef \u2026"
            else:
                self.title = "Whisper Doped"
        except Exception:
            pass

    def _mode_label(self) -> str:
        return "Mode: " + ("Push-to-talk" if self.config.mode == "push_to_talk" else "Toggle")

    # ------------------------------------------------------------------ actions
    def _toggle_mode(self, _sender) -> None:
        self.config.mode = "toggle" if self.config.mode == "push_to_talk" else "push_to_talk"
        self.config.save()
        if self.hotkeys is not None:
            self.hotkeys.mode = self.config.mode
        self.mode_item.title = self._mode_label()

    def _show_history(self, _sender) -> None:
        rows = self.store.recent(20)
        if not rows:
            rumps.alert(title="History", message="No dictations yet.")
            return
        lines = []
        for r in rows:
            ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(r.created_ts))
            lines.append(f"[{ts}] ({r.app_name or '?'}) {r.final_text}")
        rumps.Window(
            title="Recent dictations",
            message="Newest first (read-only)",
            default_text="\n".join(lines),
            dimensions=(580, 380),
        ).run()

    def _show_dictionary(self, _sender) -> None:
        current = format_terms(self.store.terms())
        resp = rumps.Window(
            title="Dictionary",
            message="Current entries:\n" + current + "\n\nAdd a word or phrase to bias recognition:",
            default_text="",
            dimensions=(440, 220),
        ).run()
        if getattr(resp, "clicked", False) and resp.text.strip():
            for line in resp.text.splitlines():
                phrase = line.strip()
                if phrase:
                    self.store.add_term(phrase, "", "vocabulary")
            rumps.alert(title="Dictionary", message="Saved.")

    def _reveal(self, _sender) -> None:
        try:
            open_folder(str(data_dir()))
        except Exception as exc:
            self.log(f"could not open folder: {exc}")

    def _about(self, _sender) -> None:
        trusted = "yes" if accessibility_trusted() else "no"
        rumps.alert(
            title="Whisper Doped",
            message=(
                "Local, private dictation.\n\n"
                f"Accessibility permission granted: {trusted}\n\n"
                "Hold Right Option to dictate (or switch to Toggle mode and press\n"
                "Ctrl+Alt+Space). Grant Microphone, Accessibility and Input\n"
                "Monitoring permissions in System Settings > Privacy & Security."
            ),
        )

    def _quit(self, _sender) -> None:
        try:
            self.dictapp.shutdown()
        except Exception:
            pass
        if self.hotkeys is not None:
            try:
                self.hotkeys.stop()
            except Exception:
                pass
        rumps.quit_application()


def run_menubar(config: Config, dictapp, hotkeys, store: Store) -> int:
    menubar = MenuBarApp(dictapp, config, store, hotkeys=hotkeys)
    dictapp.on_state = menubar.set_state

    # The overlay must be created on the main thread before the run loop starts.
    if hasattr(dictapp.overlay, "setup"):
        dictapp.overlay.setup()

    # Warm the model up in the background so the UI appears instantly.
    threading.Thread(target=dictapp.warmup, daemon=True).start()

    hotkeys.start()
    print("Whisper Doped running in the menu bar.")
    print(f"  push-to-talk : hold {config.push_to_talk_key}")
    print(f"  toggle combo : {config.toggle_combo}  (mode: {config.mode})")
    menubar.run()
    return 0
