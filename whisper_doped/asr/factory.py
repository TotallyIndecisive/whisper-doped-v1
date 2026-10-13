"""Backend selection."""

from __future__ import annotations

from typing import Optional

from ..config import Config
from .base import BaseTranscriber
from .fasterwhisper_backend import FasterWhisperTranscriber
from .mlx_backend import MLXTranscriber
from .whispercpp_backend import WhisperCppTranscriber

_BACKENDS: dict[str, type[BaseTranscriber]] = {
    "mlx": MLXTranscriber,
    "whispercpp": WhisperCppTranscriber,
    "fasterwhisper": FasterWhisperTranscriber,
}

# preference order for "auto" (fastest / most portable first)
_ORDER = ["mlx", "whispercpp", "fasterwhisper"]

_INSTALL_HINT = (
    "No speech-recognition backend is available. Install one of:\n"
    "  * Apple Silicon (fast):  pip install mlx-whisper\n"
    "  * Portable CPU:          pip install pywhispercpp\n"
    "  * Portable CPU/GPU:      pip install faster-whisper"
)


def available_backends() -> dict[str, bool]:
    return {name: cls.available() for name, cls in _BACKENDS.items()}


def resolve_backend(choice: str) -> str:
    choice = (choice or "auto").lower()
    if choice in ("auto", ""):
        for name in _ORDER:
            if _BACKENDS[name].available():
                return name
        raise RuntimeError(_INSTALL_HINT)
    if choice not in _BACKENDS:
        raise ValueError(f"unknown ASR backend: {choice!r} (choose from {', '.join(_BACKENDS)})")
    if not _BACKENDS[choice].available():
        raise RuntimeError(
            f"ASR backend {choice!r} is selected but its dependency is not installed.\n{_INSTALL_HINT}"
        )
    return choice


def model_for(config: Config, name: str) -> Optional[str]:
    return {
        "mlx": config.model,
        "whispercpp": config.whispercpp_model,
        "fasterwhisper": config.fasterwhisper_model,
    }.get(name)


def create_transcriber(config: Config) -> BaseTranscriber:
    name = resolve_backend(config.asr_backend)
    cls = _BACKENDS[name]
    return cls(
        model=model_for(config, name) or None,
        language=config.language,
        beam_size=config.beam_size,
    )
