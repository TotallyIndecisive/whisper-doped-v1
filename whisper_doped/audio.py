"""Microphone capture plus audio-file loading.

Capture mirrors the recovered ``renderer/dist/recorderWorklet.js`` behaviour: the
input is accumulated into fixed-size chunks (the original used ``chunkSize =
640``) and handed off as raw float32 PCM at 16 kHz mono, which is what Whisper
expects.

``load_audio`` is the cross-platform file loader used by the ASR backends so they
all receive plain numpy arrays and never have to know about file formats.
"""

from __future__ import annotations

import threading
from typing import Optional

import numpy as np

try:  # import lazily-ish so `--self-test` works without PortAudio installed
    import sounddevice as sd
except Exception:  # pragma: no cover - environment without PortAudio
    sd = None  # type: ignore


class MicrophoneUnavailable(RuntimeError):
    pass


class Recorder:
    """Collects PCM while ``is_recording`` is true."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_frames: int = 640,
        device: Optional[int] = None,
    ) -> None:
        if sd is None:
            raise MicrophoneUnavailable(
                "sounddevice/PortAudio is not available. Run: pip install sounddevice"
            )
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_frames = chunk_frames
        self.device = device

        self._frames: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream: "sd.InputStream | None" = None
        self._recording = False
        self._level = 0.0

    # ------------------------------------------------------------------ props
    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def level(self) -> float:
        """Most recent RMS level in 0..1 (used by the overlay meter)."""
        return self._level

    # --------------------------------------------------------------- lifecycle
    def _callback(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if not self._recording:
            return
        chunk = np.asarray(indata, dtype=np.float32).copy()
        with self._lock:
            self._frames.append(chunk)
        try:
            self._level = float(np.sqrt(np.mean(np.square(chunk)))) if chunk.size else 0.0
        except Exception:
            self._level = 0.0

    def start(self) -> None:
        if self._recording:
            return
        with self._lock:
            self._frames = []
        self._level = 0.0
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            blocksize=self.chunk_frames,
            device=self.device,
            callback=self._callback,
        )
        self._stream.start()
        self._recording = True

    def stop(self) -> np.ndarray:
        """Stop and return the captured audio as a 1-D float32 array."""
        self._recording = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None
        with self._lock:
            frames = self._frames
            self._frames = []
        if not frames:
            return np.zeros(0, dtype=np.float32)
        audio = np.concatenate(frames, axis=0)
        return audio.reshape(-1).astype(np.float32)

    def duration_seconds(self, audio: np.ndarray) -> float:
        return float(audio.shape[0]) / float(self.sample_rate)


def list_devices() -> str:
    if sd is None:
        return "sounddevice not available"
    try:
        return str(sd.query_devices())
    except Exception as exc:  # pragma: no cover
        return f"error querying devices: {exc}"


# --------------------------------------------------------------------------- files
def _resample(x: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    if src_rate == dst_rate or x.size == 0:
        return x.astype(np.float32, copy=False)
    n = int(round(x.size * dst_rate / src_rate))
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    idx = np.linspace(0.0, float(x.size - 1), n)
    return np.interp(idx, np.arange(x.size), x).astype(np.float32)


def _read_wav(path: str) -> tuple[np.ndarray, int]:
    import wave

    with wave.open(str(path), "rb") as w:
        n, sr, ch, sw = w.getnframes(), w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    if sw == 1:
        a = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif sw == 2:
        a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    elif sw == 4:
        a = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise RuntimeError(f"unsupported WAV sample width: {sw} bytes")
    if ch > 1:
        a = a.reshape(-1, ch)
    return a, sr


def _read_via_ffmpeg(path: str) -> tuple[np.ndarray, int]:
    import shutil
    import subprocess

    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "Cannot decode this audio file. Install `ffmpeg` or `soundfile` "
            "(pip install soundfile)."
        )
    cmd = ["ffmpeg", "-v", "error", "-i", str(path),
           "-f", "f32le", "-ac", "1", "-ar", "16000", "-"]
    out = subprocess.run(cmd, capture_output=True, check=True)
    return np.frombuffer(out.stdout, dtype="<f4").copy(), 16000


def load_audio(path: str, target_rate: int = 16000) -> np.ndarray:
    """Load any audio file to 16 kHz mono float32 (best-effort, no hard deps)."""
    data: Optional[np.ndarray] = None
    rate = target_rate

    if _module("soundfile"):
        try:
            import soundfile as sf  # type: ignore

            data, rate = sf.read(path, dtype="float32", always_2d=True)
        except Exception:
            data = None

    if data is None and str(path).lower().endswith(".wav"):
        try:
            data, rate = _read_wav(path)
        except Exception:
            data = None

    if data is None:
        data, rate = _read_via_ffmpeg(path)

    if data.ndim > 1:
        data = data.mean(axis=1)
    data = np.ascontiguousarray(data, dtype=np.float32)
    return _resample(data, int(rate), target_rate)


def _module(name: str) -> bool:
    import importlib.util

    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False
