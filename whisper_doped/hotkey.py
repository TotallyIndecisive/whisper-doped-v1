"""Global activation hotkeys.

Mirrors the original's keyboard service: dictate either by *holding* a key
(push-to-talk, default Right Option) or by pressing a *toggle* combination
(default Ctrl+Alt+Space).  Implemented with ``pynput``, which needs the
Accessibility permission (and, for listening, "Input Monitoring" on newer
macOS releases).
"""

from __future__ import annotations

from typing import Callable, Optional

try:
    from pynput import keyboard  # type: ignore

    _HAVE_PYNPUT = True
except Exception:  # pragma: no cover
    keyboard = None  # type: ignore
    _HAVE_PYNPUT = False


_GENERIC_MODS = {"ctrl", "alt", "cmd", "shift"}

_SPECIAL = {
    "space": "space",
    "enter": "enter",
    "return": "enter",
    "tab": "tab",
    "esc": "esc",
    "escape": "esc",
    "backspace": "backspace",
    "delete": "delete",
}


def _named_key(name: str):
    return getattr(keyboard.Key, name, None)


def _parse_token(token: str):
    token = token.strip().lower()
    if not token:
        return None
    if token in ("control", "ctrl"):
        return keyboard.Key.ctrl
    if token in ("option", "opt", "alt"):
        return keyboard.Key.alt
    if token in ("command", "cmd", "super", "meta"):
        return keyboard.Key.cmd
    if token == "shift":
        return keyboard.Key.shift
    if token in _SPECIAL:
        return _named_key(_SPECIAL[token])
    if token in ("alt_r", "alt_l", "cmd_r", "cmd_l", "ctrl_r", "ctrl_l", "shift_r", "shift_l"):
        return _named_key(token)
    if token.startswith("f") and token[1:].isdigit():
        return _named_key(token)
    if len(token) == 1:
        return keyboard.KeyCode.from_char(token)
    return None


class HotkeyManager:
    def __init__(
        self,
        mode: str = "push_to_talk",
        push_to_talk_key: str = "alt_r",
        toggle_combo: str = "ctrl+alt+space",
        on_start: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        if not _HAVE_PYNPUT:
            raise RuntimeError("pynput is not installed. Run: pip install pynput")
        self.mode = mode
        self._pt_key = _parse_token(push_to_talk_key)
        if self._pt_key is None:
            raise RuntimeError(f"unrecognised push-to-talk key: {push_to_talk_key!r}")

        self._combo_mods: set[str] = set()
        self._combo_trigger = None
        for part in toggle_combo.split("+"):
            part = part.strip()
            if not part:
                continue
            if part.lower() in ("ctrl", "control", "alt", "option", "opt", "cmd", "command", "shift"):
                canon = {
                    "control": "ctrl", "ctrl": "ctrl", "option": "alt", "opt": "alt", "alt": "alt",
                    "command": "cmd", "cmd": "cmd", "super": "cmd", "meta": "cmd", "shift": "shift",
                }[part.lower()]
                self._combo_mods.add(canon)
            else:
                self._combo_trigger = _parse_token(part)

        self.on_start = on_start or (lambda: None)
        self.on_stop = on_stop or (lambda: None)
        self.on_error = on_error or (lambda msg: None)

        self._pressed: set = set()
        self._active = False
        self._listener: "keyboard.Listener | None" = None

    # ------------------------------------------------------------------ state
    @property
    def active(self) -> bool:
        return self._active

    def set_active(self, value: bool) -> None:
        self._active = value

    # --------------------------------------------------------------- listening
    def start(self) -> None:
        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    # --------------------------------------------------------------- internals
    def _mod_active(self, name: str) -> bool:
        variants = {
            "ctrl": (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r),
            "alt": (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r),
            "cmd": (keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r),
            "shift": (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r),
        }[name]
        return any(v in self._pressed for v in variants)

    def _begin(self) -> None:
        if not self._active:
            self._active = True
            self.on_start()

    def _end(self) -> None:
        if self._active:
            self._active = False
            self.on_stop()

    def _on_press(self, key) -> None:  # noqa: ANN001
        self._pressed.add(key)
        if self.mode == "push_to_talk":
            if key == self._pt_key:
                self._begin()
            return
        # toggle mode
        if self._combo_trigger is not None and key == self._combo_trigger:
            if all(self._mod_active(m) for m in self._combo_mods):
                if self._active:
                    self._end()
                else:
                    self._begin()

    def _on_release(self, key) -> None:  # noqa: ANN001
        self._pressed.discard(key)
        if self.mode == "push_to_talk" and key == self._pt_key:
            self._end()
