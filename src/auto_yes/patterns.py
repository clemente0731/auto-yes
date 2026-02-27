"""Categorized prompt-pattern registry.

Patterns are organised by *category* so each AI CLI tool (or general purpose
prompts) lives in its own section.  ``PromptDetector`` loads one or more
categories at construction time.

Each pattern entry is a ``(regex_source, suggested_response)`` tuple.
*suggested_response* can be:

* ``None``  – use the caller's default (typically ``"y"``)
* ``"yes"`` – the prompt requires the full word
* ``""``    – just press Enter (empty response)

To add a new tool, append a new key to ``REGISTRY`` following the same
structure.  No other file needs to change.
"""

# ------------------------------------------------------------------
# generic: universal y/n / yes/no prompts (always loaded)
# ------------------------------------------------------------------
_GENERIC = {
    "description": "universal interactive prompt patterns",
    "patterns": [
        # --- [y/n] family ---
        (r"\[y/n\]", None),
        (r"\[Y/n\]", None),
        (r"\[y/N\]", None),
        (r"\[Y/N\]", None),
        (r"\(y/n\)", None),
        (r"\(Y/n\)", None),
        (r"\(y/N\)", None),
        (r"\(Y/N\)", None),

        # --- [yes/no] family ---
        (r"\[yes/no\]", "yes"),
        (r"\(yes/no\)", "yes"),
        (r"\[Yes/No\]", "yes"),

        # --- common question sentences ---
        (r"Do you want to continue\s*\?", None),
        (r"Do you wish to proceed\s*\?", None),
        (r"Are you sure\s*\?", None),
        (r"Continue\s*\?", None),
        (r"Proceed\s*\?", None),
        (r"Confirm\s*\?", None),

        # --- destructive-action prompts ---
        (r"[Oo]verwrite\b.*\?", None),
        (r"[Rr]eplace\b.*\?", None),
        (r"[Dd]elete\b.*\?", None),
        (r"[Rr]emove\b.*\?", None),

        # --- package-manager prompts ---
        (r"Is this ok\s*\[", None),
        (r"Do you want to install\b.*\?", None),

        # --- need / require prompts ---
        (r"\b[Nn]eed\s+to\b.*\?", None),
        (r"\b[Rr]equire[ds]?\b.*\?", None),
        (r"\b[Nn]ecessary\b.*\?", None),

        # --- "type yes to confirm" ---
        (r"[Tt]ype\s+'?yes'?\s+to\s+(?:continue|confirm|proceed)", "yes"),

        # --- press enter / return ---
        (r"[Pp]ress\s+(?:[Ee]nter|[Rr]eturn)\s+to\s+continue", ""),
    ],
}

# ------------------------------------------------------------------
# claude: Anthropic Claude Code CLI
# ------------------------------------------------------------------
_CLAUDE = {
    "description": "Anthropic Claude Code CLI",
    "patterns": [
        (r">\s*1\.\s*Yes,?\s+I trust this folder", None),
        (r"Do you want to use this API key\s*\?", None),
        (r">\s*1\.\s*Yes", None),
        (r"Press Enter to continue…", ""),
        (r"❯\s*1\.\s*Dark mode\s*✔", None),
    ],
}

# ------------------------------------------------------------------
# gemini: Google Gemini CLI
# ------------------------------------------------------------------
_GEMINI = {
    "description": "Google Gemini CLI",
    "patterns": [
        (r"│\s*●?\s*1\.\s*(?:Yes,?\s+)?[Aa]llow once", None),
        (r"│\s*●?\s*1\.\s*Yes", None),
    ],
}

# ------------------------------------------------------------------
# codex: OpenAI Codex CLI
# ------------------------------------------------------------------
_CODEX = {
    "description": "OpenAI Codex CLI",
    "patterns": [
        (r">\s*1\.\s*Yes", None),
        (r">\s*1\.\s*Yes,?\s+allow Codex to work", None),
        (r">\s*1\.\s*Approve and run now", None),
    ],
}

# ------------------------------------------------------------------
# copilot: GitHub Copilot CLI
# ------------------------------------------------------------------
_COPILOT = {
    "description": "GitHub Copilot CLI",
    "patterns": [
        (r"│?\s*❯?\s*1\.\s*Yes,?\s+proceed", None),
        (r"❯\s*1\.\s*Yes", None),
    ],
}

# ------------------------------------------------------------------
# cursor: Cursor Agent CLI
# ------------------------------------------------------------------
_CURSOR = {
    "description": "Cursor Agent CLI",
    "patterns": [
        (r"→\s*Run\s+\(once\)\s+\(y\)(?:\s+\(enter\))?", None),
        (r"Skip\s+\(esc\s+or\s+n\)", None),
        (r"▶\s*\[a\]\s*Trust this workspace", None),
    ],
}

# ------------------------------------------------------------------
# grok: xAI Grok CLI
# ------------------------------------------------------------------
_GROK = {
    "description": "xAI Grok CLI",
    "patterns": [
        (r"^\s*1\.\s*Yes", None),
    ],
}

# ------------------------------------------------------------------
# auggie: Augment Code CLI
# ------------------------------------------------------------------
_AUGGIE = {
    "description": "Augment Code Auggie CLI",
    "patterns": [
        (r"\[Y\]\s*Enable indexing", None),
    ],
}

# ------------------------------------------------------------------
# amp: Sourcegraph Amp CLI
# ------------------------------------------------------------------
_AMP = {
    "description": "Sourcegraph Amp CLI",
    "patterns": [
        (r"^\s{0,4}Approve\s", None),
    ],
}

# ------------------------------------------------------------------
# qwen: Alibaba Qwen Code CLI
# ------------------------------------------------------------------
_QWEN = {
    "description": "Alibaba Qwen Code CLI",
    "patterns": [],
}

# ==================================================================
# public registry – the single source of truth
# ==================================================================

REGISTRY = {
    "generic": _GENERIC,
    "claude": _CLAUDE,
    "gemini": _GEMINI,
    "codex": _CODEX,
    "copilot": _COPILOT,
    "cursor": _CURSOR,
    "grok": _GROK,
    "auggie": _AUGGIE,
    "amp": _AMP,
    "qwen": _QWEN,
}

# convenience constant: all category names except "generic"
AI_CLI_NAMES = sorted(k for k in REGISTRY if k != "generic")


def get_patterns(categories):
    """Collect ``(regex_source, response)`` tuples for the given *categories*.

    Raises ``KeyError`` for unknown category names.
    """
    result = []
    seen = set()
    for name in categories:
        for entry in REGISTRY[name]["patterns"]:
            key = entry[0]
            if key not in seen:
                seen.add(key)
                result.append(entry)
    return result


def available_categories():
    """Return a list of ``(name, description)`` for every registered category."""
    return [(k, v["description"]) for k, v in REGISTRY.items()]
