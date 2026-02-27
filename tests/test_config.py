"""Tests for auto_yes.config module."""

import json
import os
import tempfile

import auto_yes.config as cfg


class TestConfig:
    """Use a temporary config dir so tests never touch the real one."""

    def setup_method(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_dir = cfg._config_dir

        def _fake_dir():
            return self._tmpdir

        cfg._config_dir = staticmethod(_fake_dir)

    def teardown_method(self):
        cfg._config_dir = self._orig_dir
        import shutil

        shutil.rmtree(self._tmpdir, ignore_errors=True)

    # ---- load / save ----

    def test_load_defaults_when_no_file(self):
        c = cfg.load()
        assert c["response"] == "y"
        assert c["cooldown"] == 0.5
        assert c["custom_patterns"] == []

    def test_save_and_reload(self):
        data = cfg.load()
        data["response"] = "yes"
        cfg.save(data)

        reloaded = cfg.load()
        assert reloaded["response"] == "yes"

    # ---- pattern helpers ----

    def test_add_pattern_persists(self):
        cfg.add_pattern(r"my_prompt\?")
        c = cfg.load()
        assert r"my_prompt\?" in c["custom_patterns"]

    def test_add_pattern_dedup(self):
        cfg.add_pattern("dup")
        cfg.add_pattern("dup")
        c = cfg.load()
        assert c["custom_patterns"].count("dup") == 1

    def test_remove_pattern(self):
        cfg.add_pattern("gone")
        cfg.remove_pattern("gone")
        c = cfg.load()
        assert "gone" not in c["custom_patterns"]

    def test_remove_nonexistent_is_noop(self):
        cfg.remove_pattern("never_added")
        c = cfg.load()
        assert c == cfg.load()
