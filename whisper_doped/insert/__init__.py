"""Text-insertion backends.

The app asks the OS layer to type recognised text into whatever has focus. Each
backend implements:

    inserter.insert(text) -> str      # the method that succeeded, for history
    inserter.selected_text() -> str    # best-effort, may be empty
"""

from __future__ import annotations

from .factory import create_inserter

__all__ = ["create_inserter"]
