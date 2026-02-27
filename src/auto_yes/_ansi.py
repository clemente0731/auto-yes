"""ANSI escape code handling utilities.

Provides helpers to strip ANSI/VT escape sequences and control characters
so that prompt-pattern matching operates on the *visible* text only.
"""

import re

_ANSI_RE = re.compile(
    r"\x1b"
    r"(?:"
    r"\[[0-9;?]*[A-Za-z~]"  # CSI sequences (e.g. colors, cursor movement)
    r"|\][^\x07]*(?:\x07|\x1b\\)"  # OSC sequences (e.g. window title)
    r"|[()#][A-Za-z0-9]"  # character set / font selection
    r"|[A-Za-z=<>]"  # simple two-char sequences
    r")"
)

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def strip_ansi(text):
    """Remove ANSI / VT escape sequences from *text*."""
    return _ANSI_RE.sub("", text)


def strip_control(text):
    """Remove control characters except ``\\n`` (0x0a) and ``\\r`` (0x0d)."""
    return _CONTROL_RE.sub("", text)


def clean_text(text):
    """Strip escapes, resolve carriage-returns and produce clean visible text.

    For each line the last carriage-return segment wins (simulates terminal
    overwrite behaviour).
    """
    text = strip_ansi(text)
    text = strip_control(text)

    cleaned_lines = []
    for line in text.split("\n"):
        segments = line.split("\r")
        cleaned_lines.append(segments[-1])

    return "\n".join(cleaned_lines)
