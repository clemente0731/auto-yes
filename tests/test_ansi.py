"""Tests for auto_yes._ansi module."""

from auto_yes._ansi import clean_text, strip_ansi, strip_control


class TestStripAnsi:
    def test_plain_text_unchanged(self):
        assert strip_ansi("hello world") == "hello world"

    def test_removes_color_codes(self):
        colored = "\x1b[31mERROR\x1b[0m: something broke"
        assert strip_ansi(colored) == "ERROR: something broke"

    def test_removes_cursor_movement(self):
        text = "\x1b[2J\x1b[HWelcome"
        assert strip_ansi(text) == "Welcome"

    def test_removes_osc_sequences(self):
        text = "\x1b]0;My Title\x07some content"
        assert strip_ansi(text) == "some content"

    def test_empty_string(self):
        assert strip_ansi("") == ""


class TestStripControl:
    def test_preserves_newlines_and_cr(self):
        text = "line1\nline2\rline3"
        assert strip_control(text) == "line1\nline2\rline3"

    def test_removes_bell_and_backspace(self):
        text = "he\x07llo\x08"
        assert strip_control(text) == "hello"


class TestCleanText:
    def test_ansi_and_cr_combined(self):
        raw = "\x1b[32mpartial\rDo you want to continue? [y/n]\x1b[0m"
        result = clean_text(raw)
        assert "Do you want to continue? [y/n]" in result
        assert "\x1b" not in result

    def test_carriage_return_overwrites(self):
        raw = "old text\rnew text"
        assert clean_text(raw) == "new text"

    def test_multiline_preserved(self):
        raw = "line 1\nline 2\nline 3"
        assert clean_text(raw) == "line 1\nline 2\nline 3"
