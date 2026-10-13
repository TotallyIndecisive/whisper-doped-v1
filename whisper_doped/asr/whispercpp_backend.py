"""Portable CPU backend: whisper.cpp via ``pywhispercpp``."""

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from ..platform_info import module_available
from .base import BaseTranscriber, Transcript


class WhisperCppTranscriber(BaseTranscriber):
    name = "whispercpp"
    default_model = "small.en"   # a ggml model name (auto-downloaded) or a .bin path

    @classmethod
    def available(cls) -> bool:
        return module_available("pywhispercpp")

    def _load(self):
        if self._impl is None:
            from pywhispercpp.model import Model  # type: ignore

            self._impl = Model(self.model, print_realtime=False, print_progress=False)
        return self._impl

    def transcribe(self, audio: np.ndarray, initial_prompt: Optional[str] = None) -> Transcript:
        if audio is None or audio.size == 0:
            return self._empty(self.model, self.name)
        audio = np.ascontiguousarray(audio, dtype=np.float32).reshape(-1)

        with self._lock:
            model = self._load()
            started = time.perf_counter()
            params: dict = {}
            if self.language:
                params["language"] = self.language
            if initial_prompt:
                params["initial_prompt"] = initial_prompt
            segments = model.transcribe(audio, **params)
            text = "".join(getattr(s, "text", "") for s in segments).strip()
            latency_ms = int((time.perf_counter() - started) * 1000)

        return Transcript(
            text=text,
            language=self.language or None,
            latency_ms=latency_ms,
            model=self.model,
            backend=self.name,
        )
