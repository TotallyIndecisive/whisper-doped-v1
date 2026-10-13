"""The orchestrator: hotkey -> record -> transcribe -> polish -> insert -> history.

This is the local equivalent of the original Electron main process. It owns the
audio engine and coordinates the injected transcriber, polisher, inserter and
overlay. Callbacks driven by the global hotkey arrive on a background thread, so
the heavy work (transcription) always runs off the UI thread.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from . import feedback
from .asr import BaseTranscriber, create_transcriber
from .audio import Recorder
from .config import Config
from .insert import create_inserter
from .polish import Polisher
from .storage import Store
from .system import frontmost_app_name
from .ui.overlay_base import NullOverlay

StateCallback = Callable[[str], None]
TextCallback = Callable[[str, str], None]  # (raw, final)


class DictationApp:
    def __init__(
        self,
        config: Config,
        store: Store,
        *,
        transcriber: Optional[BaseTranscriber] = None,
        overlay=None,
        on_state: Optional[StateCallback] = None,
        on_text: Optional[TextCallback] = None,
        use_sounds: bool = True,
        log: Callable[[str], None] = print,
    ) -> None:
        self.config = config
        self.store = store
        self.log = log
        self.on_state = on_state or (lambda _s: None)
        self.on_text = on_text or (lambda _r, _f: None)

        self.recorder = Recorder(
            sample_rate=config.sample_rate,
            channels=config.channels,
            chunk_frames=config.chunk_frames,
            device=config.input_device,
        )
        self.transcriber = transcriber or create_transcriber(config)
        self.polisher = Polisher(
            store=store,
            spoken_punctuation=config.spoken_punctuation,
            enabled=config.polish,
            openai_api_key=config.openai_api_key,
            cloud=config.cloud_polish,
        )
        self.inserter = create_inserter(config)
        self.overlay = overlay or NullOverlay()
        self.use_sounds = use_sounds and config.play_sounds

        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None
        self._started_at = 0.0
        self._busy = False

    # ------------------------------------------------------------------ state
    @property
    def recording(self) -> bool:
        return self.recorder.is_recording

    def _set_state(self, state: str) -> None:
        try:
            self.on_state(state)
        except Exception:
            pass

    # --------------------------------------------------------------- lifecycle
    def warmup(self) -> None:
        self.log(f"Loading model ({self.transcriber.describe()})\u2026")
        try:
            self.transcriber.warmup()
            self.log("Model ready.")
        except Exception as exc:
            self.log(f"Model warmup failed: {exc}")

    def begin(self) -> None:
        with self._lock:
            if self.recorder.is_recording:
                return
            try:
                self.recorder.start()
            except Exception as exc:
                self.log(f"Microphone error: {exc}")
                self._set_state("idle")
                if self.use_sounds:
                    feedback.play("error")
                return
            self._started_at = time.perf_counter()
            if self.use_sounds:
                feedback.play("start")
            self.overlay.show("Listening\u2026")
            self._set_state("recording")
            if self.config.max_seconds > 0:
                self._timer = threading.Timer(self.config.max_seconds, self.end)
                self._timer.daemon = True
                self._timer.start()

    def end(self) -> None:
        with self._lock:
            if not self.recorder.is_recording:
                return
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            audio = self.recorder.stop()
            duration_ms = int((time.perf_counter() - self._started_at) * 1000)
            if self.use_sounds:
                feedback.play("stop")
            self.overlay.update("Transcribing\u2026")
            self._set_state("transcribing")

        thread = threading.Thread(target=self._process, args=(audio, duration_ms), daemon=True)
        thread.start()

    def toggle(self) -> None:
        if self.recorder.is_recording:
            self.end()
        else:
            self.begin()

    def _process(self, audio, duration_ms: int) -> None:
        self._busy = True
        try:
            target_app = frontmost_app_name()
            prompt = self.store.initial_prompt(self.config.extra.get("user_name", ""))
            transcript = self.transcriber.transcribe(audio, initial_prompt=prompt or None)
            raw = transcript.text
            if not raw:
                self.log("(nothing recognised)")
                self.overlay.update("Heard nothing")
                time.sleep(0.8)
                self._set_state("idle")
                return

            final = self.polisher.polish(raw)
            method = "noop"
            try:
                method = self.inserter.insert(final)
            except Exception as exc:
                self.log(f"Insertion failed: {exc}")
                if self.use_sounds:
                    feedback.play("error")

            self.store.add_history(
                raw_text=raw,
                final_text=final,
                app_name=target_app,
                duration_ms=duration_ms,
                latency_ms=transcript.latency_ms,
                model=transcript.model,
                language=transcript.language,
                insert_method=method,
            )
            try:
                self.on_text(raw, final)
            except Exception:
                pass
            self.log(f"\u2192 {final}  [{method}, {transcript.latency_ms} ms]")
            if self.use_sounds:
                feedback.play("done")
            self.overlay.update("Inserted")
            time.sleep(0.5)
        except Exception as exc:  # keep the app alive on any failure
            self.log(f"Transcription error: {exc}")
            if self.use_sounds:
                feedback.play("error")
        finally:
            self.overlay.hide()
            self._set_state("idle")
            self._busy = False

    def shutdown(self) -> None:
        try:
            if self.recorder.is_recording:
                self.recorder.stop()
        except Exception:
            pass
