# Contributing to auto-yes

Thanks for considering a contribution! Here is how to get started.

## Development setup

```bash
git clone https://github.com/clemente0731/auto-yes.git
cd auto-yes
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Running tests

```bash
# full suite
pytest

# with coverage
pytest --cov=auto_yes --cov-report=term-missing

# single file
pytest tests/test_detector.py -v
```

## Linting and formatting

The project uses [Ruff](https://docs.astral.sh/ruff/) for both linting and
formatting:

```bash
ruff check src/ tests/       # lint
ruff format src/ tests/      # format
```

Or use `pre-commit` to run everything at once:

```bash
pre-commit run --all-files
```

## Adding a new AI CLI profile

1. Open `src/auto_yes/patterns.py`.
2. Add a new `_MY_TOOL` dict with `"description"` and `"patterns"`.
3. Register it in `REGISTRY["my-tool"] = _MY_TOOL`.
4. Add tests in `tests/test_detector.py` under a new `TestMyToolPatterns` class.
5. Update the table in `README.md`.

No other files need to change.

## Commit messages

Use concise, imperative-mood messages:

```
add grok CLI pattern profile
fix cooldown check on select timeout
```

## Pull requests

- One logical change per PR.
- Include tests for new features or bug fixes.
- Make sure `ruff check` and `pytest` pass before pushing.
- Fill in the PR template description.

## Releasing (maintainers)

1. Update `version` in `pyproject.toml` and `src/auto_yes/__init__.py`.
2. Add a section to `CHANGELOG.md`.
3. Commit: `git commit -m "release v0.2.0"`.
4. Tag: `git tag v0.2.0`.
5. Push: `git push origin main --tags`.
6. Create a GitHub Release from the tag — the `publish.yml` workflow
   will upload to PyPI automatically via trusted publishing.

## Code of conduct

Be respectful and constructive. We follow the
[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
