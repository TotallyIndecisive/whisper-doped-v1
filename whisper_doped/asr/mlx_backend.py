"""Apple Silicon backend: Whisper on the GPU via MLX."""

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from ..platform_info import is_apple_silicon, module_available
from .base import BaseTranscriber, Transcript


class MLXTranscriber(BaseTranscriber):
    name = "mlx"
    default_model = "mlx-community/whisper-large-v3-turbo"

    @classmethod
    def available(cls) -> bool:
        return is_apple_silicon() and module_available("mlx_whisper")

    def _load(self):
        if self._impl is None:
            import mlx_whisper  # type: ignore

            self._impl = mlx_whisper
        return self._impl

    def transcribe(self, audio: np.ndarray, initial_prompt: Optional[str] = None) -> Transcript:
        if audio is None or audio.size == 0:
            return self._empty(self.model, self.name)
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)

        with self._lock:
            impl = self._load()
            started = time.perf_counter()
            kwargs = {"path_or_hf_repo": self.model, "word_timestamps": False}
            if self.language:
                kwargs["language"] = self.language
            if initial_prompt:
                kwargs["initial_prompt"] = initial_prompt
            result = impl.transcribe(audio, **kwargs)
            latency_ms = int((time.perf_counter() - started) * 1000)

        return Transcript(
            text=(result.get("text") or "").strip(),
            language=result.get("language"),
            segments=result.get("segments") or [],
            latency_ms=latency_ms,
            model=self.model,
            backend=self.name,
        )
