"""Portable backend: faster-whisper (CTranslate2), CPU or CUDA."""

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from ..platform_info import module_available
from .base import BaseTranscriber, Transcript


class FasterWhisperTranscriber(BaseTranscriber):
    name = "fasterwhisper"
    default_model = "small"   # e.g. tiny, base, small, medium, large-v3

    @classmethod
    def available(cls) -> bool:
        return module_available("faster_whisper")

    def _load(self):
        if self._impl is None:
            from faster_whisper import WhisperModel  # type: ignore

            self._impl = WhisperModel(self.model, device="auto", compute_type="auto")
        return self._impl

    def transcribe(self, audio: np.ndarray, initial_prompt: Optional[str] = None) -> Transcript:
        if audio is None or audio.size == 0:
            return self._empty(self.model, self.name)
        audio = np.ascontiguousarray(audio, dtype=np.float32).reshape(-1)

        with self._lock:
            model = self._load()
            started = time.perf_counter()
            segments, info = model.transcribe(
                audio,
                language=self.language,
                beam_size=self.beam_size,
                initial_prompt=initial_prompt,
                vad_filter=True,
            )
            # ``segments`` is a generator: force it here while we hold the lock.
            text = "".join(seg.text for seg in segments).strip()
            latency_ms = int((time.perf_counter() - started) * 1000)
            language = getattr(info, "language", None)

        return Transcript(
            text=text,
            language=language,
            latency_ms=latency_ms,
            model=self.model,
            backend=self.name,
        )
