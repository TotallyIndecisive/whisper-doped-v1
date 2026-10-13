"""Speech recognition backends.

Each backend implements the same tiny interface so the rest of the app never
cares where transcription happens:

    transcriber = create_transcriber(config)
    result = transcriber.transcribe(float32_16k_audio, initial_prompt=...)

Backends shipped:
    mlx            - Apple Silicon GPU via mlx-whisper (fastest on Macs)
    whispercpp     - whisper.cpp via pywhispercpp (portable CPU)
    fasterwhisper  - CTranslate2 via faster-whisper (portable CPU/CUDA)
"""

from __future__ import annotations

from .base import BaseTranscriber, Transcript
from .factory import available_backends, create_transcriber

__all__ = ["BaseTranscriber", "Transcript", "create_transcriber", "available_backends"]
