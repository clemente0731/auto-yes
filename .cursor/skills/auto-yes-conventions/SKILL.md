---
name: auto-yes-conventions
description: Project conventions and coding standards for the auto-yes CLI tool. Use when editing any file in this project, adding new patterns, modifying CI/CD, or reviewing code changes.
---

# auto-yes Project Conventions

## Communication

- Respond and explain in Chinese; write all code and comments in English only.
- For C++/Python language feature terms, use the original keyword (e.g. "decorator", "closure", "RAII") instead of a Chinese translation.

## Code Style

### General

- No ternary expressions (`SIM108` is ignored in ruff config).
- Prioritize readability: avoid chaining multiple syntactic sugars on a single line.
- Comments in English, lowercase first letter (e.g. `# validate input before sending`).
- Prefer f-strings over `.format()` (ruff `UP032`).
- Use `contextlib.suppress(OSError)` instead of `try-except-pass` (ruff `SIM105`).
- Use `OSError` instead of aliased exceptions like `select.error` (ruff `UP024`).
- Remove redundant `"r"` mode in `open()` calls (ruff `UP015`).

### Regex Patterns (`patterns.py`)

- Literal Unicode characters (`❯`, `✔`) are allowed; suppress linter with `# noqa: RUF001`.
- In test files, use `\u276f` escape for the same characters to avoid linter noise.
- Pattern response conventions:
  - `None` — send the default response (usually `"y"`)
  - `"yes"` — send the full word `"yes"` (for SSH fingerprints, terraform, etc.)
  - `""` — send an empty line / press Enter (for "press enter to continue")
- Every new pattern **must** have a corresponding test in `tests/test_detector.py`.

## Safety

- Add safety checks or raise errors at dangerous code paths; never silently swallow failures.
- Dangerous actions are **excluded** from default generic patterns:
  `overwrite`, `replace`, `delete`, `remove`, `upgrade`, `update`,
  `merge`, `restart`, `reboot`, `install`.
  Users can opt-in via `--pattern` if needed.
- Do not auto-confirm pip install/uninstall prompts by default.

## Project Setup

- Python `>= 3.10` only (`requires-python`, ruff `target-version`, mypy `python_version`).
- Linter: ruff (check + format). See `pyproject.toml [tool.ruff]` for full config.
- Tests: pytest with `tests/` directory.

## CI/CD (GitHub Actions)

- The `lint` job is **report-only** (`continue-on-error: true`, `|| true`). Lint failures must not block the pipeline.
- All job failure logs are uploaded as artifacts and aggregated in a `failure-summary` job.
- `ci.yml` is a reusable workflow (called by `publish.yml` as a gate before PyPI release).
- PyPI publishing uses OIDC trusted publishers (no API tokens).

## CLI Design

- **Recommended mode**: `auto-yes <profile> [args...]` — single-process wrap, verbose by default.
- **Advanced mode**: `auto-yes --on --cli <name>` — global shell session.
- The `--on` / `run` modes default to verbose off; wrap mode defaults to verbose on.
- `auto-yes list` (`-l`, `--list`) enumerates available profiles.
