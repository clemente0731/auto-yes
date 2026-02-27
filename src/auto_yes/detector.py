"""Prompt detection engine.

Scans terminal output for interactive yes/no prompts and determines the
appropriate auto-response.  Patterns are loaded from ``patterns.py`` by
category (e.g. ``"generic"``, ``"claude"``, ``"codex"``).
"""

import re
from collections import namedtuple

from auto_yes._ansi import clean_text
from auto_yes.patterns import REGISTRY, get_patterns

DetectionResult = namedtuple("DetectionResult", ["pattern", "suggested_response"])


class PromptDetector:
    """Detect interactive prompts in terminal output.

    Parameters
    ----------
    categories : list[str] or None
        Pattern categories to load (default ``["generic"]``).
        Pass ``["generic", "claude"]`` to also match Claude-specific prompts.
    extra_patterns : list[str] or None
        Additional raw regex strings supplied by the user at runtime.

    Only the *last* non-empty line of the text is inspected so that prompts
    embedded in normal program output do not cause false positives.
    """

    def __init__(self, categories=None, extra_patterns=None):
        if categories is None:
            categories = ["generic"]

        self._entries = []
        self._load_categories(categories)

        for pat in extra_patterns or []:
            self._entries.append((re.compile(pat, re.IGNORECASE), pat, None))

    # ------------------------------------------------------------------
    # loading
    # ------------------------------------------------------------------

    def _load_categories(self, categories):
        seen = set()
        for src, response in get_patterns(categories):
            if src in seen:
                continue
            seen.add(src)
            self._entries.append((re.compile(src, re.IGNORECASE), src, response))

    def load_category(self, name):
        """Add all patterns from *name* that are not already registered."""
        existing = {src for _, src, _ in self._entries}
        for src, response in REGISTRY[name]["patterns"]:
            if src not in existing:
                self._entries.append((re.compile(src, re.IGNORECASE), src, response))
                existing.add(src)

    # ------------------------------------------------------------------
    # detection
    # ------------------------------------------------------------------

    def detect(self, raw_text):
        """Return a ``DetectionResult`` if the tail of *raw_text* looks like
        a prompt waiting for user input, otherwise ``None``.
        """
        text = clean_text(raw_text)

        lines = text.rstrip().split("\n")
        if not lines:
            return None

        last_line = lines[-1]
        if not last_line.strip():
            return None

        # only inspect the last visible line (the one the cursor is on)
        # if a prompt appeared on an earlier line and further output followed,
        # the process already moved past that prompt
        for compiled, source, response in self._entries:
            if compiled.search(last_line):
                return DetectionResult(pattern=source, suggested_response=response)

        return None

    # ------------------------------------------------------------------
    # runtime mutation
    # ------------------------------------------------------------------

    def add_pattern(self, pattern_str, response=None):
        """Register an additional pattern at runtime."""
        self._entries.append((re.compile(pattern_str, re.IGNORECASE), pattern_str, response))

    @property
    def pattern_strings(self):
        """Return a list of all registered pattern source strings."""
        return [source for _, source, _ in self._entries]
