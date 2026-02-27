"""Persistent configuration for auto-yes.

Config lives at ``~/.config/auto-yes/config.json`` on Unix or
``%APPDATA%/auto-yes/config.json`` on Windows.
"""

import json
import os

_DIR_NAME = "auto-yes"
_FILE_NAME = "config.json"

_DEFAULTS = {
    "custom_patterns": [],
    "response": "y",
    "cooldown": 0.5,
    "verbose": False,
}


def _config_dir():
    if os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get(
            "XDG_CONFIG_HOME",
            os.path.join(os.path.expanduser("~"), ".config"),
        )
    return os.path.join(base, _DIR_NAME)


def _config_path():
    return os.path.join(_config_dir(), _FILE_NAME)


# ------------------------------------------------------------------
# public helpers
# ------------------------------------------------------------------

def load():
    """Load config from disk, falling back to defaults for missing keys."""
    path = _config_path()
    if not os.path.isfile(path):
        return dict(_DEFAULTS)

    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    merged = dict(_DEFAULTS)
    merged.update(data)
    return merged


def save(cfg):
    """Persist *cfg* dict to the config file."""
    dir_path = _config_dir()
    os.makedirs(dir_path, exist_ok=True)

    with open(_config_path(), "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def add_pattern(pattern):
    """Append *pattern* to the custom-patterns list (deduplicated)."""
    cfg = load()
    if pattern not in cfg["custom_patterns"]:
        cfg["custom_patterns"].append(pattern)
        save(cfg)
    return cfg


def remove_pattern(pattern):
    """Remove *pattern* from the custom-patterns list if present."""
    cfg = load()
    if pattern in cfg["custom_patterns"]:
        cfg["custom_patterns"].remove(pattern)
        save(cfg)
    return cfg


def config_path():
    """Return the resolved path to the config file (for display)."""
    return _config_path()
