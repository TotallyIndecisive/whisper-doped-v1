"""Unit tests for the deterministic polish rules and the local store."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from whisper_doped.polish import (
    Polisher,
    capitalize_sentences,
    collapse_repetitions,
    ensure_terminal_punctuation,
    remove_fillers,
    tidy_whitespace,
)
from whisper_doped.storage import Store


class TestPolishPieces(unittest.TestCase):
    def test_remove_fillers(self):
        self.assertEqual(remove_fillers("um so uh I was, um, thinking").split(), ["so", "I", "was,", "thinking"])

    def test_collapse_repetitions(self):
        self.assertEqual(collapse_repetitions("the the the cat"), "the cat")
        self.assertEqual(collapse_repetitions("I think I think we should"), "I think we should")

    def test_capitalize(self):
        self.assertEqual(capitalize_sentences("hello world. next one."), "Hello world. Next one.")
        self.assertEqual(capitalize_sentences("i am i"), "I am I")

    def test_terminal_punctuation(self):
        self.assertEqual(ensure_terminal_punctuation("done"), "done.")
        self.assertEqual(ensure_terminal_punctuation("done!"), "done!")

    def test_tidy(self):
        self.assertEqual(tidy_whitespace("a  ,  b"), "a, b")


class TestPolisher(unittest.TestCase):
    def setUp(self):
        self.p = Polisher()

    def test_full_pipeline(self):
        self.assertEqual(
            self.p.polish("um so the the meeting is at 5 actually 6pm"),
            "So the meeting is at 6pm.",
        )

    def test_spoken_punctuation(self):
        self.assertEqual(self.p.polish("hello comma world period"), "Hello, world.")

    def test_no_polish(self):
        p = Polisher(enabled=False)
        self.assertEqual(p.polish("hello   comma world"), "hello comma world")

    def test_dictionary_replacement(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td) / "t.sqlite")
            store.add_term("my email", "sam@example.com", "replacement")
            p = Polisher(store=store)
            self.assertEqual(p.polish("send it to my email"), "Send it to sam@example.com.")


class TestStore(unittest.TestCase):
    def test_history_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td) / "t.sqlite")
            store.add_history("raw text", "Final text.", app_name="Editor")
            rows = store.recent()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].final_text, "Final text.")
            self.assertEqual(rows[0].app_name, "Editor")

    def test_vocabulary_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td) / "t.sqlite")
            store.add_term("Kubernetes", "", "vocabulary")
            store.add_term("whisper doped", "Whisper Doped", "replacement")
            prompt = store.initial_prompt("Sam")
            self.assertIn("Kubernetes", prompt)
            self.assertIn("Sam", prompt)

    def test_cross_thread_access(self):
        """The store is used from transcription worker threads, not just the UI thread."""
        import threading

        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td) / "t.sqlite")
            store.add_term("Kubernetes", "", "vocabulary")
            errors: list[Exception] = []

            def worker():
                try:
                    store.initial_prompt("Sam")          # read
                    store.add_history("raw", "final")    # write
                    store.apply_replacements("hello")
                except Exception as exc:  # pragma: no cover
                    errors.append(exc)

            threads = [threading.Thread(target=worker) for _ in range(4)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(errors, [])
            self.assertEqual(store.history_count(), 4)


if __name__ == "__main__":
    unittest.main()
