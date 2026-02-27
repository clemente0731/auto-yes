# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-02-27

### Added

- Cursor Agent CLI: `Skip (esc or n)` pattern for approval dialog last-line detection
- Cursor Agent CLI: support `→ Run (once) (y)` variant without `(enter)` suffix
- Generic: `need to ...?`, `require(d/s) ...?`, `necessary ...?` prompt patterns
- CI/CD: `publish.yml` workflow for automated PyPI release on version tags
- CI: `workflow_call` trigger so publish workflow can reuse full CI as gate

### Fixed

- Cursor Agent CLI: approval dialog was missed when `Skip (esc or n)` was the last visible line

## [0.1.0] - 2025-02-27

### Added

- PTY proxy runner with transparent I/O forwarding (Unix `pty` + `select`)
- Windows support via `pywinpty` with subprocess pipe fallback
- Smart prompt detection on the last visible line (avoids false positives)
- 25 built-in generic patterns (`[y/n]`, `Continue?`, `Are you sure?`, etc.)
- Categorized AI CLI profiles: Claude, Gemini, Codex, Copilot, Cursor, Grok, Auggie, Amp, Qwen
- `auto-yes --on` interactive shell session mode
- `auto-yes run -- CMD` single-command wrapper mode
- `auto-yes patterns [CATEGORY...]` pattern inspection
- `auto-yes add-pattern` / `del-pattern` persistent custom patterns
- Persistent configuration at `~/.config/auto-yes/config.json`
- ANSI escape code stripping for clean pattern matching
- Cooldown timer to prevent duplicate responses
- SIGWINCH forwarding for terminal resize propagation
- `--cli NAME` flag to load AI-tool-specific patterns
- `--verbose` mode showing each auto-response
- PEP 561 `py.typed` marker

[Unreleased]: https://github.com/clemente0731/auto-yes/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/clemente0731/auto-yes/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/clemente0731/auto-yes/releases/tag/v0.1.0
