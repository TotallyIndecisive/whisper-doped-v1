"""Local persistence: dictation history + personal dictionary.

The original ships ~60 SQL migrations that create ``flow.sqlite`` with
``history``, ``dictionary``, ``tone_match`` and friends. We keep the two tables
that make dictation feel personal: ``history`` (what you said) and
``dictionary`` (vocabulary to bias the recognizer + replacements/snippets to
expand afterwards).

Threading: the store is created on the UI thread but used from transcription
worker threads, so the connection is opened with ``check_same_thread=False`` and
every operation is serialised with a re-entrant lock.
"""

from __future__ import annotations

import re
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_ts    REAL NOT NULL,
    raw_text      TEXT NOT NULL,
    final_text    TEXT NOT NULL,
    app_name      TEXT,
    duration_ms   INTEGER,
    latency_ms    INTEGER,
    model         TEXT,
    language      TEXT,
    insert_method TEXT
);
CREATE TABLE IF NOT EXISTS dictionary (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    phrase      TEXT NOT NULL UNIQUE,
    replacement TEXT NOT NULL DEFAULT '',
    kind        TEXT NOT NULL DEFAULT 'vocabulary',   -- vocabulary | replacement | snippet
    use_count   INTEGER NOT NULL DEFAULT 0,
    created_ts  REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_history_ts ON history(created_ts DESC);
"""

_WORD_BOUNDARY = r"(?<!\w){}(?!\w)"


@dataclass
class HistoryRow:
    id: int
    created_ts: float
    raw_text: str
    final_text: str
    app_name: Optional[str]
    duration_ms: Optional[int]
    latency_ms: Optional[int]
    model: Optional[str]
    language: Optional[str]
    insert_method: Optional[str]


@dataclass
class Term:
    id: int
    phrase: str
    replacement: str
    kind: str
    use_count: int


class Store:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Shared across threads: allow cross-thread use and serialise access.
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.executescript(_SCHEMA)
            self.conn.execute(
                "INSERT OR IGNORE INTO meta(key, value) VALUES('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
            self.conn.commit()

    # ------------------------------------------------------------------ history
    def add_history(
        self,
        raw_text: str,
        final_text: str,
        *,
        app_name: Optional[str] = None,
        duration_ms: Optional[int] = None,
        latency_ms: Optional[int] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        insert_method: Optional[str] = None,
    ) -> int:
        with self._lock:
            cur = self.conn.execute(
                """INSERT INTO history
                   (created_ts, raw_text, final_text, app_name, duration_ms,
                    latency_ms, model, language, insert_method)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (time.time(), raw_text, final_text, app_name, duration_ms,
                 latency_ms, model, language, insert_method),
            )
            self.conn.commit()
            return int(cur.lastrowid)

    def recent(self, limit: int = 50) -> list[HistoryRow]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM history ORDER BY created_ts DESC LIMIT ?", (limit,)
            ).fetchall()
        return [HistoryRow(**dict(r)) for r in rows]

    def history_count(self) -> int:
        with self._lock:
            return int(self.conn.execute("SELECT COUNT(*) FROM history").fetchone()[0])

    # -------------------------------------------------------------- dictionary
    def add_term(self, phrase: str, replacement: str = "", kind: str = "vocabulary") -> None:
        phrase = phrase.strip()
        if not phrase:
            return
        with self._lock:
            self.conn.execute(
                """INSERT INTO dictionary(phrase, replacement, kind, created_ts)
                   VALUES(?,?,?,?)
                   ON CONFLICT(phrase) DO UPDATE SET
                       replacement=excluded.replacement,
                       kind=excluded.kind""",
                (phrase, replacement, kind, time.time()),
            )
            self.conn.commit()

    def remove_term(self, phrase: str) -> None:
        with self._lock:
            self.conn.execute("DELETE FROM dictionary WHERE phrase = ?", (phrase,))
            self.conn.commit()

    def terms(self, kind: Optional[str] = None) -> list[Term]:
        with self._lock:
            if kind:
                rows = self.conn.execute(
                    "SELECT * FROM dictionary WHERE kind=? ORDER BY phrase", (kind,)
                ).fetchall()
            else:
                rows = self.conn.execute(
                    "SELECT * FROM dictionary ORDER BY kind, phrase"
                ).fetchall()
        return [Term(r["id"], r["phrase"], r["replacement"], r["kind"], r["use_count"]) for r in rows]

    def _bump(self, phrase: str) -> None:
        with self._lock:
            self.conn.execute(
                "UPDATE dictionary SET use_count = use_count + 1 WHERE phrase = ?", (phrase,)
            )
            self.conn.commit()

    # ------------------------------------------------------------- vocabulary
    def vocabulary(self) -> list[str]:
        """Words/phrases used to bias the recognizer (Whisper initial_prompt)."""
        return [t.phrase for t in self.terms("vocabulary")]

    def initial_prompt(self, user_name: str = "") -> str:
        parts = [p for p in [user_name, *self.vocabulary()] if p]
        return ", ".join(parts)

    # ------------------------------------------------- replacements/snippets
    def apply_replacements(self, text: str) -> str:
        if not text:
            return text
        # Explicit replacements first (longest phrase wins), then snippets.
        terms = self.terms("replacement") + self.terms("snippet")
        terms.sort(key=lambda t: len(t.phrase), reverse=True)
        for t in terms:
            if not t.phrase:
                continue
            pattern = re.compile(_WORD_BOUNDARY.format(re.escape(t.phrase)), re.IGNORECASE)
            new_text, n = pattern.subn(t.replacement, text)
            if n:
                text = new_text
                self._bump(t.phrase)
        return text

    # ------------------------------------------------------------------ misc
    def close(self) -> None:
        with self._lock:
            self.conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def format_terms(terms: Iterable[Term]) -> str:
    lines = []
    for t in terms:
        if t.kind == "vocabulary":
            lines.append(f"  vocabulary   {t.phrase}")
        else:
            lines.append(f"  {t.kind:<11} {t.phrase}  ->  {t.replacement}")
    return "\n".join(lines) if lines else "  (empty)"
