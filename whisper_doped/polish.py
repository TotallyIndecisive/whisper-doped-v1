"""Text polish / formatting.

The original calls ``/llm/polish_text`` and ``/llm/formatting`` on a server.
This module reproduces the *behaviour* locally with deterministic rules:

  * remove filler words ("um", "uh", ...)
  * collapse repeated words ("the the" -> "the")
  * apply spoken punctuation ("hello comma world" -> "hello, world")
  * honour "scratch that" (delete the previous sentence)
  * fix simple self-corrections ("at 5 actually 6pm" -> "at 6pm")
  * capitalise sentences and end with punctuation
  * expand personal dictionary replacements / snippets

An optional cloud pass is available if you set an OpenAI key, but the app is
fully functional without it.
"""

from __future__ import annotations

import re
from typing import Optional

FILLERS = {
    "um", "uh", "umm", "uhh", "uhm", "erm", "er", "ermm",
    "hmm", "hmmm", "mm", "mmm", "mhm", "eh", "ah", "ahh", "uh-huh",
}

# spoken -> literal. Longest phrases are matched first.
SPOKEN_PUNCTUATION: dict[str, str] = {
    "new paragraph": "\n\n",
    "new line": "\n",
    "exclamation mark": "!",
    "exclamation point": "!",
    "question mark": "?",
    "full stop": ".",
    "open parenthesis": "(",
    "open paren": "(",
    "close parenthesis": ")",
    "close paren": ")",
    "open quote": '"',
    "close quote": '"',
    "semicolon": ";",
    "ellipsis": "\u2026",
    "period": ".",
    "comma": ",",
    "colon": ":",
    "dash": " - ",
}

# punctuation that attaches to the previous word with no leading space
_ATTACHING = set(".,?!:;)]\u2026")


def remove_fillers(text: str) -> str:
    if not text:
        return text
    pattern = re.compile(r"(?<!\w)(" + "|".join(re.escape(f) for f in FILLERS) + r")(?!\w)[,]?", re.IGNORECASE)
    return pattern.sub("", text)


def collapse_repetitions(text: str) -> str:
    # single words: "the the the" -> "the"
    text = re.sub(r"\b(\w+)(?:\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    # two/three word phrases: "I think I think" -> "I think"
    text = re.sub(r"\b(\w+(?:\s+\w+){1,2})(?:\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    return text


def apply_spoken_punctuation(text: str) -> str:
    if not text:
        return text
    for phrase in sorted(SPOKEN_PUNCTUATION, key=len, reverse=True):
        repl = SPOKEN_PUNCTUATION[phrase]
        word = re.escape(phrase)
        if repl in _ATTACHING:
            # remove any preceding space so the mark hugs the word
            pat = re.compile(r"\s*(?<!\w)" + word + r"(?!\w)", re.IGNORECASE)
        elif repl == "(":
            pat = re.compile(r"\s*(?<!\w)" + word + r"(?!\w)\s*", re.IGNORECASE)
        elif repl.startswith("\n"):
            pat = re.compile(r"\s*(?<!\w)" + word + r"(?!\w)\s*", re.IGNORECASE)
        else:  # dash
            pat = re.compile(r"\s*(?<!\w)" + word + r"(?!\w)\s*", re.IGNORECASE)
        text = pat.sub(repl, text)
    return text


def handle_scratch_that(text: str) -> str:
    # "I went to the store scratch that" -> "" ; "hello scratch that goodbye" -> "goodbye"
    return re.sub(r"^.*?\bscratch that\b[.,!?]?\s*", "", text, flags=re.IGNORECASE | re.DOTALL)


def apply_self_corrections(text: str) -> str:
    # "at 5 actually 6pm" -> "at 6pm"; "the 3rd no wait the 4th" -> "the 4th"
    cue = r"(?:actually|no,?\s+wait|i mean|rather|make that)"
    # numeric false starts
    text = re.sub(
        r"\b\d[\d:]*(?:\s*(?:am|pm|o'?clock))?\s*,?\s*" + cue + r"\s*,?\s+(?=\d)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # repeated definite article false starts: "the red the blue" -> "the blue"
    text = re.sub(r"\bthe\s+\w+\s*,?\s*" + cue + r"\s*,?\s+(the\b)", r"\1", text, flags=re.IGNORECASE)
    return text


def tidy_whitespace(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)          # no space before punctuation
    text = re.sub(r"([,;])(?=\S)", r"\1 ", text)          # space after , ; (not : , to protect times/URLs)
    text = re.sub(r"(?<=[.!?])(?=[A-Z])", " ", text)      # split sentences, but not inside emails/domains
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def capitalize_sentences(text: str) -> str:
    if not text:
        return text
    # A sentence boundary is [.!?] followed by whitespace (or a newline), so we
    # do not uppercase the "com" in "example.com" or the "co" in "a.co".
    parts = re.split(r"([.!?]+[ \t]+|\n+)", text)
    out: list[str] = []
    for i, chunk in enumerate(parts):
        if i % 2 == 1:                     # the delimiters
            out.append(chunk)
            continue
        if not chunk:
            out.append(chunk)
            continue
        # capitalise first alphabetic character of the chunk
        m = re.search(r"[A-Za-z]", chunk)
        if m:
            idx = m.start()
            chunk = chunk[:idx] + chunk[idx].upper() + chunk[idx + 1:]
        out.append(chunk)
    text = "".join(out)
    # standalone "i" -> "I"
    text = re.sub(r"\bi\b", "I", text)
    return text


def ensure_terminal_punctuation(text: str) -> str:
    if text and re.search(r"[A-Za-z0-9]$", text):
        text += "."
    return text


class Polisher:
    def __init__(self, store=None, spoken_punctuation: bool = True, enabled: bool = True,
                 openai_api_key: str = "", cloud: bool = False) -> None:
        self.store = store
        self.spoken_punctuation = spoken_punctuation
        self.enabled = enabled
        self._cloud = cloud
        self._openai_key = openai_api_key

    def polish(self, raw: str) -> str:
        text = raw or ""
        if self.store is not None:
            text = self.store.apply_replacements(text)
        if not self.enabled:
            return tidy_whitespace(text)

        text = handle_scratch_that(text)
        text = remove_fillers(text)
        text = collapse_repetitions(text)
        text = apply_self_corrections(text)
        if self.spoken_punctuation:
            text = apply_spoken_punctuation(text)
        text = tidy_whitespace(text)
        text = capitalize_sentences(text)
        text = ensure_terminal_punctuation(text)

        if self._cloud and self._openai_key:
            text = self._cloud_polish(text)
        return text

    # ------------------------------------------------------------ optional LLM
    def _cloud_polish(self, text: str) -> str:
        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI(api_key=self._openai_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content":
                     "Clean up this dictated text: fix punctuation, casing and obvious "
                     "recognition slips. Do not add or remove meaning. Return only the text."},
                    {"role": "user", "content": text},
                ],
                temperature=0,
            )
            return (resp.choices[0].message.content or text).strip()
        except Exception:
            return text
