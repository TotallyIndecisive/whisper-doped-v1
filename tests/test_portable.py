"""Tests for the portable layers: platform detection, ASR/insertion factories,
config round-trip, and the audio-file loader."""

from __future__ import annotations

import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from whisper_doped import platform_info as pf


class TestPlatformInfo(unittest.TestCase):
    def test_basic_booleans(self):
        self.assertIsInstance(pf.is_macos(), bool)
        self.assertIsInstance(pf.is_linux(), bool)
        self.assertIsInstance(pf.is_apple_silicon(), bool)

    def test_module_available(self):
        self.assertTrue(pf.module_available("numpy"))
        self.assertFalse(pf.module_available("definitely_not_a_module_xyz"))


class TestConfigRoundtrip(unittest.TestCase):
    def test_roundtrip_with_new_fields(self):
        import whisper_doped.config as cfg

        with tempfile.TemporaryDirectory() as td:
            cfg.CONFIG_PATH = Path(td) / "config.json"
            cfg.DB_PATH = Path(td) / "t.sqlite"
            c = cfg.Config()
            c.asr_backend = "whispercpp"
            c.whispercpp_model = "base.en"
            c.insert_backend = "linux"
            c.save()
            again = cfg.Config.load()
            self.assertEqual(again.asr_backend, "whispercpp")
            self.assertEqual(again.whispercpp_model, "base.en")
            self.assertEqual(again.insert_backend, "linux")

    def test_load_missing_file_returns_defaults(self):
        import whisper_doped.config as cfg

        with tempfile.TemporaryDirectory() as td:
            cfg.CONFIG_PATH = Path(td) / "nope.json"
            c = cfg.Config.load()
            self.assertEqual(c.asr_backend, "auto")
            self.assertEqual(c.model, "mlx-community/whisper-large-v3-turbo")


class TestAsrFactory(unittest.TestCase):
    def test_unknown_backend_raises(self):
        from whisper_doped.asr.factory import resolve_backend

        with self.assertRaises(ValueError):
            resolve_backend("bogus")
        with self.assertRaises(ValueError):
            resolve_backend("nosuch")

    def test_resolve_auto_never_crashes(self):
        from whisper_doped.asr.factory import resolve_backend

        try:
            name = resolve_backend("auto")
            self.assertIn(name, {"mlx", "whispercpp", "fasterwhisper"})
        except RuntimeError:
            # no backend installed on this machine: acceptable, but still not a crash
            pass

    def test_model_for_uses_per_backend_field(self):
        from whisper_doped.asr.factory import model_for
        from whisper_doped.config import Config

        c = Config()
        c.whispercpp_model = "base.en"
        c.fasterwhisper_model = "medium"
        self.assertEqual(model_for(c, "whispercpp"), "base.en")
        self.assertEqual(model_for(c, "fasterwhisper"), "medium")
        self.assertEqual(model_for(c, "mlx"), c.model)

    def test_available_backends_is_a_dict(self):
        from whisper_doped.asr import available_backends

        d = available_backends()
        self.assertEqual(set(d), {"mlx", "whispercpp", "fasterwhisper"})


class TestInsertFactory(unittest.TestCase):
    def test_forced_null_backend(self):
        from whisper_doped.config import Config
        from whisper_doped.insert.factory import create_inserter

        c = Config()
        c.insert_backend = "null"
        ins = create_inserter(c)
        self.assertEqual(ins.name, "null")
        self.assertEqual(ins.insert("hello"), "noop")
        self.assertTrue(ins.available())

    def test_auto_resolves_to_something(self):
        from whisper_doped.config import Config
        from whisper_doped.insert.factory import create_inserter

        ins = create_inserter(Config())
        self.assertIn(ins.name, {"macos", "linux", "null"})


class TestLoadAudio(unittest.TestCase):
    def _write_wav(self, path: Path, rate: int, seconds: float, freq: float = 440.0) -> None:
        n = int(rate * seconds)
        t = np.linspace(0, seconds, n, endpoint=False)
        signal = (0.3 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
        pcm = (signal * 32767).astype("<i2")
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(pcm.tobytes())

    def test_load_16k_wav(self):
        from whisper_doped.audio import load_audio

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "in.wav"
            self._write_wav(p, 16000, 1.0)
            audio = load_audio(p)
            self.assertEqual(audio.dtype, np.float32)
            self.assertEqual(audio.ndim, 1)
            self.assertAlmostEqual(audio.shape[0] / 16000, 1.0, delta=0.01)

    def test_load_resamples_to_16k(self):
        from whisper_doped.audio import load_audio

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "high.wav"
            self._write_wav(p, 48000, 1.0)
            audio = load_audio(p)
            self.assertAlmostEqual(audio.shape[0] / 16000, 1.0, delta=0.05)


if __name__ == "__main__":
    unittest.main()