"""Common interface shared by every speech-recognition backend."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np


@dataclass
class Transcript:
    text: str
    language: Optional[str] = None
    segments: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: int = 0
    model: str = ""
    duration_s: float = 0.0
    backend: str = ""


class BaseTranscriber:
    """Base class: subclasses provide ``_load`` and ``transcribe``."""

    name = "base"
    default_model = ""

    def __init__(self, model: Optional[str] = None, language: Optional[str] = None, beam_size: int = 1) -> None:
        self.model = model or self.default_model
        self.language = language
        self.beam_size = beam_size
        self._impl = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------- capability
    @classmethod
    def available(cls) -> bool:
        """Whether this backend's dependency is installed and usable here."""
        return False

    def describe(self) -> str:
        return f"{self.name} ({self.model})"

    # -------------------------------------------------------------- lifecycle
    def warmup(self) -> None:
        """Load weights so the first real dictation is not slow."""
        try:
            self.transcribe(np.zeros(16000, dtype=np.float32))
        except Exception:
            pass

    # -------------------------------------------------------------- inference
    def transcribe(self, audio: np.ndarray, initial_prompt: Optional[str] = None) -> Transcript:
        raise NotImplementedError

    def transcribe_file(self, path: str, initial_prompt: Optional[str] = None) -> Transcript:
        from ..audio import load_audio

        return self.transcribe(load_audio(path), initial_prompt=initial_prompt)

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _empty(model: str, backend: str) -> Transcript:
        return Transcript(text="", model=model, backend=backend)


def now_ms() -> int:
    return int(time.perf_counter() * 1000)
