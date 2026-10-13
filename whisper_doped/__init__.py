"""Whisper Doped - a local, private dictation app.

A clean-room reimplementation of the *dictation* half of Wispr Flow, built from
the architecture recovered by reverse engineering the original bundle:

    mic capture (AudioWorklet, 640-frame PCM)
        -> local ASR (the original streams to Baseten/OpenAI; we run Whisper locally)
        -> text polish / formatting (the original uses /llm/polish_text)
        -> insertion into the focused app
           (macOS: Accessibility direct-set first, clipboard + synthetic Cmd+V
            fallback with a concealed pasteboard type, then clipboard restore;
            Linux: wtype/xdotool direct typing with clipboard fallback)

The speech engine is pluggable:

    mlx            Apple Silicon GPU via mlx-whisper  (pip install mlx-whisper)
    whispercpp     whisper.cpp via pywhispercpp        (pip install pywhispercpp)
    fasterwhisper  CTranslate2 via faster-whisper      (pip install faster-whisper)

Server-side pieces (sign-in, accounts, sync, Notetaker, meetings, telemetry) are
intentionally omitted - everything runs locally.
"""

__version__ = "0.2.0"
__all__ = ["__version__"]