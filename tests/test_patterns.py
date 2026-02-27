"""Tests for auto_yes.patterns module."""

from auto_yes.patterns import (
    AI_CLI_NAMES,
    REGISTRY,
    available_categories,
    get_patterns,
)


class TestRegistry:
    def test_generic_exists(self):
        assert "generic" in REGISTRY

    def test_all_ai_names_in_registry(self):
        for name in AI_CLI_NAMES:
            assert name in REGISTRY

    def test_generic_not_in_ai_names(self):
        assert "generic" not in AI_CLI_NAMES

    def test_every_entry_has_description(self):
        for name, entry in REGISTRY.items():
            assert "description" in entry, f"{name} missing description"
            assert isinstance(entry["description"], str)

    def test_every_entry_has_patterns_list(self):
        for name, entry in REGISTRY.items():
            assert "patterns" in entry, f"{name} missing patterns"
            assert isinstance(entry["patterns"], list)

    def test_pattern_tuples_are_valid(self):
        for name, entry in REGISTRY.items():
            for item in entry["patterns"]:
                assert isinstance(item, tuple), f"{name}: not a tuple"
                assert len(item) == 2, f"{name}: expected 2-tuple"
                src, resp = item
                assert isinstance(src, str)
                assert resp is None or isinstance(resp, str)


class TestGetPatterns:
    def test_generic_returns_nonempty(self):
        pats = get_patterns(["generic"])
        assert len(pats) > 0

    def test_multiple_categories(self):
        generic_only = get_patterns(["generic"])
        combined = get_patterns(["generic", "claude"])
        assert len(combined) >= len(generic_only)

    def test_deduplication(self):
        pats = get_patterns(["generic", "generic"])
        sources = [p[0] for p in pats]
        assert len(sources) == len(set(sources))

    def test_unknown_category_raises(self):
        import pytest

        with pytest.raises(KeyError):
            get_patterns(["nonexistent"])


class TestAvailableCategories:
    def test_returns_list_of_tuples(self):
        cats = available_categories()
        assert len(cats) > 0
        for name, desc in cats:
            assert isinstance(name, str)
            assert isinstance(desc, str)

    def test_contains_generic(self):
        names = [name for name, _ in available_categories()]
        assert "generic" in names
