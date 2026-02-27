"""Tests for auto_yes.detector module."""

from auto_yes.detector import PromptDetector


# ==================================================================
# generic patterns (always loaded)
# ==================================================================

class TestGenericBrackets:
    def setup_method(self):
        self.det = PromptDetector()

    def test_y_n_lower(self):
        assert self.det.detect("Continue? [y/n]") is not None

    def test_Y_n(self):
        assert self.det.detect("Proceed? [Y/n]") is not None

    def test_y_N(self):
        assert self.det.detect("Delete file? [y/N]") is not None

    def test_parens_y_n(self):
        assert self.det.detect("Remove package? (y/n)") is not None

    def test_yes_no_brackets(self):
        result = self.det.detect("Overwrite config? [yes/no]")
        assert result is not None
        assert result.suggested_response == "yes"

    def test_yes_no_parens(self):
        result = self.det.detect("Replace all? (yes/no)")
        assert result is not None
        assert result.suggested_response == "yes"


class TestGenericSentences:
    def setup_method(self):
        self.det = PromptDetector()

    def test_do_you_want_to_continue(self):
        assert self.det.detect("Do you want to continue?") is not None

    def test_are_you_sure(self):
        assert self.det.detect("Are you sure?") is not None

    def test_proceed_question(self):
        assert self.det.detect("Proceed?") is not None

    def test_overwrite_file(self):
        assert self.det.detect("Overwrite output.txt?") is not None

    def test_remove_directory(self):
        assert self.det.detect("Remove directory /tmp/foo?") is not None


class TestGenericSpecial:
    def setup_method(self):
        self.det = PromptDetector()

    def test_type_yes_to_continue(self):
        result = self.det.detect("Type 'yes' to continue:")
        assert result is not None
        assert result.suggested_response == "yes"

    def test_press_enter(self):
        result = self.det.detect("Press Enter to continue")
        assert result is not None
        assert result.suggested_response == ""

    def test_is_this_ok(self):
        assert self.det.detect("Is this ok [y/d/N]:") is not None


class TestNeedRequirePrompts:
    def setup_method(self):
        self.det = PromptDetector()

    def test_need_to_install(self):
        assert self.det.detect("Need to install the following packages?") is not None

    def test_do_you_need_to(self):
        assert self.det.detect("Do you need to download dependencies?") is not None

    def test_required_question(self):
        assert self.det.detect("Installation required?") is not None

    def test_requires_question(self):
        assert self.det.detect("This action requires elevated access, continue?") is not None

    def test_necessary_question(self):
        assert self.det.detect("Is this step necessary?") is not None

    def test_need_no_question_mark_no_match(self):
        assert self.det.detect("You will need to restart later.") is None


# ==================================================================
# false-positive prevention
# ==================================================================

class TestNoFalsePositives:
    def setup_method(self):
        self.det = PromptDetector()

    def test_empty_string(self):
        assert self.det.detect("") is None

    def test_whitespace_only(self):
        assert self.det.detect("   \n   \n") is None

    def test_regular_output_with_newline(self):
        text = "Setting y/n flag in config\nDone.\n"
        assert self.det.detect(text) is None

    def test_prompt_in_middle_not_at_tail(self):
        text = "Question: continue? [y/n]\nUser chose yes.\nProcessing...\n"
        assert self.det.detect(text) is None


# ==================================================================
# AI CLI categories
# ==================================================================

class TestClaudePatterns:
    def setup_method(self):
        self.det = PromptDetector(categories=["generic", "claude"])

    def test_trust_folder(self):
        assert self.det.detect(" > 1. Yes, I trust this folder") is not None

    def test_api_key(self):
        assert self.det.detect("Do you want to use this API key?") is not None

    def test_numbered_yes(self):
        assert self.det.detect("> 1. Yes") is not None


class TestGeminiPatterns:
    def setup_method(self):
        self.det = PromptDetector(categories=["generic", "gemini"])

    def test_allow_once(self):
        assert self.det.detect("│ ● 1. Allow once") is not None

    def test_yes_allow(self):
        assert self.det.detect("│ ● 1. Yes, allow once") is not None


class TestCodexPatterns:
    def setup_method(self):
        self.det = PromptDetector(categories=["generic", "codex"])

    def test_approve_and_run(self):
        assert self.det.detect("> 1. Approve and run now") is not None

    def test_yes_allow_codex(self):
        assert self.det.detect("> 1. Yes, allow Codex to work") is not None


class TestCursorPatterns:
    def setup_method(self):
        self.det = PromptDetector(categories=["generic", "cursor"])

    def test_run_once_with_enter(self):
        assert self.det.detect("→ Run (once) (y) (enter)") is not None

    def test_run_once_without_enter(self):
        assert self.det.detect("→ Run (once) (y)") is not None

    def test_run_once_inside_box(self):
        assert self.det.detect(" │  → Run (once) (y) (enter)  │") is not None

    def test_run_once_inside_box_no_enter(self):
        assert self.det.detect(" │  → Run (once) (y)  │") is not None

    def test_skip_esc_or_n(self):
        assert self.det.detect("    Skip (esc or n)") is not None

    def test_skip_inside_box(self):
        assert self.det.detect(" │    Skip (esc or n)      ") is not None

    def test_approval_dialog_last_line_is_skip(self):
        text = (
            " Waiting for approval...\n"
            " │ Run this command?\n"
            " │  → Run (once) (y) (enter)\n"
            " │    Skip (esc or n)      "
        )
        assert self.det.detect(text) is not None

    def test_trust_workspace(self):
        assert self.det.detect("▶ [a] Trust this workspace") is not None


class TestCopilotPatterns:
    def setup_method(self):
        self.det = PromptDetector(categories=["generic", "copilot"])

    def test_yes_proceed(self):
        assert self.det.detect("│ ❯ 1. Yes, proceed") is not None


class TestLoadAll:
    def test_all_categories_loadable(self):
        from auto_yes.patterns import REGISTRY
        all_cats = list(REGISTRY.keys())
        det = PromptDetector(categories=all_cats)
        assert len(det.pattern_strings) > 0

    def test_generic_still_works_with_all(self):
        from auto_yes.patterns import REGISTRY
        det = PromptDetector(categories=list(REGISTRY.keys()))
        assert det.detect("Continue? [y/n]") is not None


# ==================================================================
# custom patterns & runtime mutation
# ==================================================================

class TestCustomPatterns:
    def test_extra_pattern_init(self):
        det = PromptDetector(extra_patterns=[r"custom_prompt\?"])
        assert det.detect("custom_prompt?") is not None

    def test_add_pattern_runtime(self):
        det = PromptDetector()
        assert det.detect("do_thing?") is None
        det.add_pattern(r"do_thing\?")
        assert det.detect("do_thing?") is not None

    def test_load_category_runtime(self):
        det = PromptDetector()
        assert det.detect("> 1. Yes, I trust this folder") is None
        det.load_category("claude")
        assert det.detect("> 1. Yes, I trust this folder") is not None

    def test_pattern_strings_includes_custom(self):
        det = PromptDetector(extra_patterns=[r"my_pat"])
        assert r"my_pat" in det.pattern_strings


class TestAnsiInPrompt:
    def test_colored_prompt_detected(self):
        det = PromptDetector()
        colored = "\x1b[1;33mContinue? [y/n]\x1b[0m"
        assert det.detect(colored) is not None
