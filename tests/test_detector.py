"""Tests for auto_yes.detector module."""

from auto_yes.detector import PromptDetector  # noqa: I001


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

    def test_conda_default_y(self):
        assert self.det.detect("Proceed ([y]/n)?") is not None

    def test_conda_default_n(self):
        assert self.det.detect("Proceed (y/[n])?") is not None

    def test_standalone_y_npm(self):
        assert self.det.detect("Ok to proceed? (y)") is not None

    def test_bare_y_n(self):
        assert self.det.detect("Continue? y/n:") is not None

    def test_bare_y_n_no_colon(self):
        assert self.det.detect("Continue? y/n") is not None

    def test_bracket_yes_no_style(self):
        assert self.det.detect("[Y]es / [N]o") is not None

    def test_bracket_yes_lower_no_style(self):
        assert self.det.detect("[Y]es / [n]o") is not None


class TestGenericSentences:
    def setup_method(self):
        self.det = PromptDetector()

    def test_do_you_want_to_continue(self):
        assert self.det.detect("Do you want to continue?") is not None

    def test_are_you_sure(self):
        assert self.det.detect("Are you sure?") is not None

    def test_proceed_question(self):
        assert self.det.detect("Proceed?") is not None

    def test_overwrite_excluded(self):
        assert self.det.detect("Overwrite output.txt?") is None

    def test_remove_excluded(self):
        assert self.det.detect("Remove directory /tmp/foo?") is None

    def test_would_you_like_to(self):
        assert self.det.detect("Would you like to install it?") is not None

    def test_do_you_agree(self):
        assert self.det.detect("Do you agree to the terms?") is not None

    def test_do_you_accept(self):
        assert self.det.detect("Do you accept the license?") is not None


class TestGenericSSH:
    def setup_method(self):
        self.det = PromptDetector()

    def test_ssh_yes_no(self):
        prompt = "Are you sure you want to " "continue connecting (yes/no)?"
        result = self.det.detect(prompt)
        assert result is not None
        assert result.suggested_response == "yes"

    def test_ssh_yes_no_fingerprint(self):
        prompt = "Are you sure you want to " "continue connecting (yes/no/[fingerprint])?"
        result = self.det.detect(prompt)
        assert result is not None
        assert result.suggested_response == "yes"


class TestGenericActionVerbs:
    def setup_method(self):
        self.det = PromptDetector()

    def test_allow(self):
        assert self.det.detect("Allow access to /tmp?") is not None

    def test_approve(self):
        assert self.det.detect("Approve this change?") is not None

    def test_accept(self):
        assert self.det.detect("Accept incoming connection?") is not None

    def test_download(self):
        assert self.det.detect("Download 150MB package?") is not None

    def test_upgrade_excluded(self):
        assert self.det.detect("Upgrade to version 3.0?") is None

    def test_update_excluded(self):
        assert self.det.detect("Update all packages?") is None

    def test_enable(self):
        assert self.det.detect("Enable auto-updates?") is not None

    def test_install_excluded(self):
        assert self.det.detect("Install missing dependencies?") is None

    def test_create(self):
        assert self.det.detect("Create directory /opt/app?") is not None

    def test_merge_excluded(self):
        assert self.det.detect("Merge branch 'feature' into main?") is None

    def test_restart_excluded(self):
        assert self.det.detect("Restart the service?") is None

    def test_reboot_excluded(self):
        assert self.det.detect("Reboot now?") is None


class TestGenericLicenseAgreement:
    def setup_method(self):
        self.det = PromptDetector()

    def test_accept_license(self):
        assert self.det.detect("Accept the license agreement") is not None

    def test_agree_to_terms(self):
        assert self.det.detect("Agree to the terms of service") is not None


class TestGenericSpecial:
    def setup_method(self):
        self.det = PromptDetector()

    def test_type_yes_to_continue(self):
        result = self.det.detect("Type 'yes' to continue:")
        assert result is not None
        assert result.suggested_response == "yes"

    def test_type_uppercase_yes(self):
        result = self.det.detect("Type 'YES' to confirm:")
        assert result is not None
        assert result.suggested_response == "yes"

    def test_enter_yes_to_confirm(self):
        result = self.det.detect("Enter 'yes' to proceed:")
        assert result is not None
        assert result.suggested_response == "yes"

    def test_terraform_only_yes_accepted(self):
        result = self.det.detect("Only 'yes' will be accepted to confirm.")
        assert result is not None
        assert result.suggested_response == "yes"

    def test_press_enter(self):
        result = self.det.detect("Press Enter to continue")
        assert result is not None
        assert result.suggested_response == ""

    def test_press_any_key(self):
        result = self.det.detect("Press any key to continue")
        assert result is not None
        assert result.suggested_response == ""

    def test_default_y_paren(self):
        result = self.det.detect("Use cache? (default: Y)")
        assert result is not None
        assert result.suggested_response == ""

    def test_default_yes_bracket(self):
        result = self.det.detect("Use cache? [default=yes]")
        assert result is not None
        assert result.suggested_response == ""

    def test_is_this_ok(self):
        assert self.det.detect("Is this ok [y/d/N]:") is not None

    def test_ok_to_proceed(self):
        assert self.det.detect("Ok to proceed?") is not None


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

    def test_plain_statement(self):
        assert self.det.detect("Downloading files...") is None

    def test_progress_line(self):
        assert self.det.detect("Installing: 45% complete") is None


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

    def test_yes_allow(self):
        assert self.det.detect("\u276f Yes, allow this tool") is not None

    def test_allow_once(self):
        assert self.det.detect("> Allow once") is not None


class TestGeminiPatterns:
    def setup_method(self):
        self.det = PromptDetector(categories=["generic", "gemini"])

    def test_allow_once(self):
        assert self.det.detect("│ ● 1. Allow once") is not None

    def test_yes_allow(self):
        assert self.det.detect("│ ● 1. Yes, allow once") is not None

    def test_allow_for_session(self):
        assert self.det.detect("│ ● 2. Allow for this session") is not None

    def test_always_allow(self):
        assert self.det.detect("│ ● 3. Always allow") is not None


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

    def test_run_always(self):
        assert self.det.detect("→ Run (always) (a)") is not None

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
        assert self.det.detect("│ \u276f 1. Yes, proceed") is not None

    def test_allow_copilot(self):
        assert self.det.detect("Allow Copilot to run this command?") is not None


class TestAiderPatterns:
    def setup_method(self):
        self.det = PromptDetector(categories=["generic", "aider"])

    def test_yes_no_style(self):
        assert self.det.detect("Run shell command? (Y)es/(N)o/(D)on't ask again [Yes]:") is not None

    def test_add_to_chat(self):
        assert self.det.detect("Add main.py to the chat?") is not None

    def test_run_shell_command(self):
        assert self.det.detect("Run shell command?") is not None

    def test_apply_edit(self):
        assert self.det.detect("Apply edit to src/utils.py?") is not None

    def test_create_new_file(self):
        assert self.det.detect("Create new file tests/test_api.py?") is not None

    def test_fix_lint(self):
        assert self.det.detect("Attempt to fix lint errors?") is not None

    def test_drop_from_chat(self):
        assert self.det.detect("Drop old_file.py from the chat?") is not None


class TestOpenHandsPatterns:
    def setup_method(self):
        self.det = PromptDetector(categories=["generic", "openhands"])

    def test_execute_action(self):
        assert self.det.detect("Do you want to execute this action?") is not None

    def test_approve(self):
        assert self.det.detect("> Approve") is not None


class TestWindsurfPatterns:
    def setup_method(self):
        self.det = PromptDetector(categories=["generic", "windsurf"])

    def test_accept_changes(self):
        assert self.det.detect("Accept all changes?") is not None

    def test_run_command(self):
        assert self.det.detect("Run this command?") is not None


class TestQwenPatterns:
    def setup_method(self):
        self.det = PromptDetector(categories=["generic", "qwen"])

    def test_numbered_yes(self):
        assert self.det.detect("> 1. Yes") is not None

    def test_approve_execution(self):
        assert self.det.detect("Approve execution?") is not None


class TestAmazonQPatterns:
    def setup_method(self):
        self.det = PromptDetector(categories=["generic", "amazonq"])

    def test_approve_action(self):
        assert self.det.detect("Do you approve this action?") is not None

    def test_accept_suggestion(self):
        assert self.det.detect("Accept suggestion?") is not None


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

    def test_all_categories_no_empty(self):
        from auto_yes.patterns import REGISTRY

        for name, entry in REGISTRY.items():
            assert len(entry["patterns"]) > 0, f"category '{name}' has no patterns"


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
