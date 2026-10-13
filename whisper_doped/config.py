"""Configuration and on-disk locations.

Mirrors the original app's preference surface (the parts that matter for
dictation) and stores everything under the OS-appropriate user data directory:

    macOS : ~/Library/Application Support/WhisperDoped
    Linux : $XDG_DATA_HOME/WhisperDoped  (default ~/.local/share/WhisperDoped)
    other : ~/.whisper-doped

Set ``WHISPER_DOPED_HOME`` to override.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Optional

APP_NAME = "WhisperDoped"


def data_dir() -> Path:
    """Location of the app's private data (history + dictionary live here)."""
    override = os.environ.get("WHISPER_DOPED_HOME")
    if override:
        base = Path(override).expanduser()
    elif os.name == "posix" and os.uname().sysname == "Darwin":
        base = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        base = (Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share") / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


CONFIG_PATH = data_dir() / "config.json"
DB_PATH = data_dir() / "whisper_doped.sqlite"


@dataclass
class Config:
    # ---- audio ---------------------------------------------------------
    sample_rate: int = 16000          # 16 kHz mono is what ASR models expect
    channels: int = 1
    chunk_frames: int = 640           # original recorderWorklet used chunkSize=640
    input_device: Optional[int] = None
    max_seconds: float = 120.0        # safety auto-stop

    # ---- activation ----------------------------------------------------
    mode: str = "push_to_talk"        # "push_to_talk" | "toggle"
    push_to_talk_key: str = "alt_r"   # hold Right Option to talk
    toggle_combo: str = "ctrl+alt+space"

    # ---- speech recognition -------------------------------------------
    asr_backend: str = "auto"         # auto | mlx | whispercpp | fasterwhisper
    model: str = "mlx-community/whisper-large-v3-turbo"   # MLX repo
    whispercpp_model: str = "small.en"                    # ggml name or .bin path
    fasterwhisper_model: str = "small"                    # HF/ct2 model name
    language: Optional[str] = None    # None = auto-detect
    beam_size: int = 1

    # ---- text handling -------------------------------------------------
    polish: bool = True               # remove fillers, fix repeats, punctuate
    spoken_punctuation: bool = True   # "comma" -> ","
    insert_backend: str = "auto"      # auto | macos | linux | null
    insert_method: str = "auto"       # macOS strategy: auto | ax | clipboard
    restore_clipboard: bool = True
    paste_delay: float = 0.18

    # ---- experience ----------------------------------------------------
    ui: str = "auto"                  # auto | menubar | console
    play_sounds: bool = True
    show_overlay: bool = True
    show_menu_bar: bool = True

    # ---- optional cloud (off by default; the app is fully local) -------
    openai_api_key: str = ""
    cloud_polish: bool = False

    extra: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    @classmethod
    def load(cls) -> "Config":
        if CONFIG_PATH.exists():
            try:
                raw = json.loads(CONFIG_PATH.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                raw = {}
            known = {f.name for f in fields(cls)}
            clean = {k: v for k, v in raw.items() if k in known}
            return cls(**clean)
        return cls()

    def save(self) -> None:
        tmp = CONFIG_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), "utf-8")
        tmp.replace(CONFIG_PATH)

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        self.save()
