"""Categorized prompt-pattern registry.

Patterns are organised by *category* so each AI CLI tool (or general purpose
prompts) lives in its own section.  ``PromptDetector`` loads one or more
categories at construction time.

Each pattern entry is a ``(regex_source, suggested_response)`` tuple.
*suggested_response* can be:

* ``None``  - use the caller's default (typically ``"y"``)
* ``"yes"`` - the prompt requires the full word
* ``""``    - just press Enter (empty response)

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
        # --- conda-style default markers: ([y]/n), (y/[n]) ---
        (r"\(\[y\]/n\)", None),
        (r"\(y/\[n\]\)", None),
        # --- standalone (y) suffix (npm "Ok to proceed? (y)") ---
        (r"\?\s*\(y\)\s*$", None),
        # --- bare y/n without brackets ---
        (r"\?\s*y/n\s*:?\s*$", None),
        # --- [Y]es / [N]o style ---
        (r"\[Y\]es\s*/\s*\[N\]o", None),
        (r"\[Y\]es\s*/\s*\[n\]o", None),
        # --- SSH / GPG host-key fingerprint confirmation ---
        (r"continue connecting\s*\(yes/no(?:/\[fingerprint\])?\)", "yes"),
        # --- common question sentences ---
        (r"Do you want to continue\s*\?", None),
        (r"Do you wish to proceed\s*\?", None),
        (r"Are you sure\s*\?", None),
        (r"Continue\s*\?", None),
        (r"Proceed\s*\?", None),
        (r"Confirm\s*\?", None),
        (r"[Ww]ould you like to\b.*\?", None),
        (r"Do you (?:agree|accept)\b.*\?", None),
        # --- safe action-verb prompts (ending with ?) ---
        (r"[Aa]llow\b.*\?", None),
        (r"[Aa]pprove\b.*\?", None),
        (r"[Aa]ccept\b.*\?", None),
        (r"[Dd]ownload\b.*\?", None),
        (r"[Ee]nable\b.*\?", None),
        (r"[Cc]reate\b.*\?", None),
        # --- dangerous actions excluded from defaults ---
        # overwrite / replace / delete / remove / upgrade / update /
        # merge / restart / reboot / install: too risky for auto-confirm
        # use --pattern to add them manually if needed
        # --- license / agreement prompts ---
        (r"[Aa]ccept\s+(?:the\s+)?license\b", None),
        (r"[Aa]gree\s+to\s+(?:the\s+)?terms\b", None),
        # --- package-manager prompts (pip excluded to avoid accidental uninstall) ---
        (r"Is this ok\s*\[", None),
        # --- need / require prompts ---
        (r"\b[Nn]eed\s+to\b.*\?", None),
        (r"\b[Rr]equire[ds]?\b.*\?", None),
        (r"\b[Nn]ecessary\b.*\?", None),
        # --- "type yes to confirm" (IGNORECASE covers YES/Yes/yes variants) ---
        (r"[Tt]ype\s+'?(?:yes|YES)'?\s+to\s+(?:continue|confirm|proceed)", "yes"),
        (r"[Ee]nter\s+'?(?:yes|YES)'?\s+to\s+(?:continue|confirm|proceed)", "yes"),
        # --- terraform-style: only 'yes' will be accepted ---
        (r"[Oo]nly\s+'?yes'?\s+will be accepted", "yes"),
        # --- press enter / return / any key ---
        (r"[Pp]ress\s+(?:[Ee]nter|[Rr]eturn)\s+to\s+continue", ""),
        (r"[Pp]ress\s+any\s+key\s+to\s+continue", ""),
        # --- (default: Y) / [default=yes] style ---
        (r"\?\s*\(default:\s*[Yy](?:es)?\)", ""),
        (r"\?\s*\[default[=:]\s*[Yy](?:es)?\]", ""),
    ],
}

# ------------------------------------------------------------------
# claude: Anthropic Claude Code CLI
# ------------------------------------------------------------------
_CLAUDE = {
    "description": "Anthropic Claude Code CLI",
    "command": ["claude"],
    "patterns": [
        (r">\s*1\.\s*Yes,?\s+I trust this folder", None),
        (r"Do you want to use this API key\s*\?", None),
        (r">\s*1\.\s*Yes", None),
        (r"Press Enter to continue…", ""),
        (r"❯\s*1\.\s*Dark mode\s*✔", None),  # noqa: RUF001
        (r"❯?\s*Yes,?\s+allow", None),  # noqa: RUF001
        (r">\s*Allow\s+(?:once|always)", None),
    ],
}

# ------------------------------------------------------------------
# gemini: Google Gemini CLI
# ------------------------------------------------------------------
_GEMINI = {
    "description": "Google Gemini CLI",
    "command": ["gemini"],
    "patterns": [
        (r"│\s*●?\s*1\.\s*(?:Yes,?\s+)?[Aa]llow once", None),
        (r"│\s*●?\s*1\.\s*Yes", None),
        (r"│\s*●?\s*2\.\s*[Aa]llow for this session", None),
        (r"│\s*●?\s*3\.\s*[Aa]lways allow", None),
    ],
}

# ------------------------------------------------------------------
# codex: OpenAI Codex CLI
# ------------------------------------------------------------------
_CODEX = {
    "description": "OpenAI Codex CLI",
    "command": ["codex"],
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
    "command": ["gh", "copilot"],
    "patterns": [
        (r"│?\s*❯?\s*1\.\s*Yes,?\s+proceed", None),  # noqa: RUF001
        (r"❯\s*1\.\s*Yes", None),  # noqa: RUF001
        (r"Allow Copilot to run\b.*\?", None),
    ],
}

# ------------------------------------------------------------------
# cursor: Cursor Agent CLI
# ------------------------------------------------------------------
_CURSOR = {
    "description": "Cursor Agent CLI",
    "command": ["agent"],
    "patterns": [
        (r"→\s*Run\s+\(once\)\s+\(y\)(?:\s+\(enter\))?", None),
        (r"→\s*Run\s+\(always\)\s+\(a\)", None),
        (r"Skip\s+\(esc\s+or\s+n\)", None),
        (r"▶\s*\[a\]\s*Trust this workspace", None),
    ],
}

# ------------------------------------------------------------------
# grok: xAI Grok CLI
# ------------------------------------------------------------------
_GROK = {
    "description": "xAI Grok CLI",
    "command": ["grok"],
    "patterns": [
        (r"^\s*1\.\s*Yes", None),
    ],
}

# ------------------------------------------------------------------
# auggie: Augment Code CLI
# ------------------------------------------------------------------
_AUGGIE = {
    "description": "Augment Code Auggie CLI",
    "command": ["auggie"],
    "patterns": [
        (r"\[Y\]\s*Enable indexing", None),
    ],
}

# ------------------------------------------------------------------
# amp: Sourcegraph Amp CLI
# ------------------------------------------------------------------
_AMP = {
    "description": "Sourcegraph Amp CLI",
    "command": ["amp"],
    "patterns": [
        (r"^\s{0,4}Approve\s", None),
    ],
}

# ------------------------------------------------------------------
# aider: Aider AI coding assistant
# ------------------------------------------------------------------
_AIDER = {
    "description": "Aider AI coding assistant",
    "command": ["aider"],
    "patterns": [
        (r"\(Y\)es/\(N\)o", None),
        (r"Add .+ to the chat\?", None),
        (r"Run shell command\?", None),
        (r"Apply edit to\b.*\?", None),
        (r"Create new file\b.*\?", None),
        (r"Attempt to fix lint errors\?", None),
        (r"Drop .+ from the chat\?", None),
    ],
}

# ------------------------------------------------------------------
# openhands: OpenHands (formerly OpenDevin) AI agent
# ------------------------------------------------------------------
_OPENHANDS = {
    "description": "OpenHands AI agent",
    "command": ["openhands"],
    "patterns": [
        (r"Do you want to execute this action\s*\?", None),
        (r">\s*Approve", None),
    ],
}

# ------------------------------------------------------------------
# windsurf: Codeium Windsurf / Cascade CLI
# ------------------------------------------------------------------
_WINDSURF = {
    "description": "Codeium Windsurf / Cascade CLI",
    "command": ["windsurf"],
    "patterns": [
        (r"Accept (?:all )?changes\s*\?", None),
        (r"Run this command\s*\?", None),
    ],
}

# ------------------------------------------------------------------
# qwen: Alibaba Qwen Code CLI
# ------------------------------------------------------------------
_QWEN = {
    "description": "Alibaba Qwen Code CLI",
    "command": ["qwen"],
    "patterns": [
        (r">\s*1\.\s*Yes", None),
        (r"Approve execution\s*\?", None),
    ],
}

# ------------------------------------------------------------------
# amazonq: Amazon Q Developer CLI
# ------------------------------------------------------------------
_AMAZONQ = {
    "description": "Amazon Q Developer CLI",
    "command": ["q"],
    "patterns": [
        (r"Do you approve this action\s*\?", None),
        (r"Accept\s+suggestion\s*\?", None),
    ],
}

# ==================================================================
# public registry - the single source of truth
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
    "aider": _AIDER,
    "openhands": _OPENHANDS,
    "windsurf": _WINDSURF,
    "qwen": _QWEN,
    "amazonq": _AMAZONQ,
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


def get_command(profile):
    """Return the real CLI command (as a list) for the given *profile*.

    Falls back to ``[profile]`` if no ``command`` field is defined.
    """
    entry = REGISTRY.get(profile)
    if entry is None:
        return [profile]
    return list(entry.get("command", [profile]))


def available_categories():
    """Return a list of ``(name, description)`` for every registered category."""
    return [(k, v["description"]) for k, v in REGISTRY.items()]
