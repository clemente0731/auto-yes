# auto-yes

> Automatically respond **yes** to interactive CLI prompts.

`auto-yes` wraps your shell or a single command inside a **PTY proxy**, watches
the output for common interactive prompts (`[y/n]`, `Continue?`, etc.) and
injects the appropriate response — all without stealing your stdin or breaking
colours, progress bars or tab-completion.

## Installation

```bash
pip install auto-yes
```

On **Windows** the tool falls back to a basic pipe-based mode.  For full PTY
support install the optional extra:

```bash
pip install auto-yes[windows]
```

## Quick start

### Shell session mode

Start a new shell where every interactive prompt is answered automatically:

```bash
auto-yes --on
# you are now inside an auto-yes shell
apt install nginx          # [y/n] → y  (auto)
pip install flask          # Proceed? → y  (auto)
exit                       # leave the session
```

### Single command mode

Wrap one command without entering a persistent session:

```bash
auto-yes run -- apt install nginx
auto-yes run -- pip install flask
```

### Check status

```bash
auto-yes status        # → "active" or "inactive"
```

## How it works

```
User terminal  ←→  PTY proxy (auto-yes)  ←→  Child process
                    │
                    ├─ reads child stdout
                    ├─ strips ANSI escapes
                    ├─ matches prompt patterns
                    ├─ injects "y\n" / "yes\n" / "\n"
                    └─ forwards everything to user
```

1. A **pseudo-terminal pair** (master/slave) is created.  The child process
   (your shell or command) is spawned on the slave side, so it believes it is
   running in a real terminal.

2. The parent process sits on the master side, using `select()` to multiplex
   user input and child output in real time.

3. Each chunk of child output is appended to a rolling buffer.  The buffer is
   cleaned (ANSI stripped, carriage-returns resolved) and checked against a set
   of **regex patterns**.

4. When a match is found on the **last visible line** (i.e. the process is
   actually waiting for input), the configured response is written into the
   master fd — the child sees it as if the user typed it.

5. A **cooldown** timer prevents responding twice to the same prompt.

6. **SIGWINCH** is forwarded so terminal resizes propagate correctly.

## CLI reference

```
auto-yes --on [OPTIONS]            start an auto-yes shell session
auto-yes --off                     exit info
auto-yes status                    check if auto-yes is active
auto-yes run [OPTIONS] -- CMD...   run a single command with auto-yes
auto-yes patterns [CATEGORY...]    list prompt patterns (optionally filtered)
auto-yes add-pattern PATTERN       persist a custom regex pattern
auto-yes del-pattern PATTERN       remove a custom pattern
```

### Options (for `--on` and `run`)

| Flag | Description | Default |
|------|-------------|---------|
| `--response TEXT` | Text to send when a prompt is detected | `y` |
| `--cooldown FLOAT` | Seconds between auto-responses | `0.5` |
| `--verbose`, `-v` | Print a notice each time auto-yes responds | off |
| `--pattern REGEX` | Extra prompt pattern (repeatable) | — |
| `--cli NAME` | AI CLI profile to load (repeatable, or `all`) | — |

## Pattern categories

Patterns are organized by category for maintainability.  The `generic` category
is **always loaded**.  AI CLI profiles are opt-in via `--cli`.

### generic (always loaded)

| Type | Examples |
|------|----------|
| Bracket choices | `[y/n]`, `[Y/n]`, `(y/N)`, `[yes/no]` |
| Question sentences | `Continue?`, `Proceed?`, `Are you sure?` |
| Destructive prompts | `Overwrite file?`, `Remove directory?`, `Delete …?` |
| Package managers | `Is this ok [y/d/N]`, `Do you want to install …?` |
| Full-word yes | `Type 'yes' to continue` → responds `yes` |
| Press enter | `Press Enter to continue` → responds with empty line |

### AI CLI profiles

| Profile | Tool | Key patterns |
|---------|------|-------------|
| `claude` | Anthropic Claude Code | `1. Yes, I trust this folder`, API key prompt |
| `gemini` | Google Gemini CLI | `1. Allow once`, `1. Yes` |
| `codex` | OpenAI Codex CLI | `1. Approve and run now`, `1. Yes` |
| `copilot` | GitHub Copilot CLI | `1. Yes, proceed` |
| `cursor` | Cursor Agent CLI | `Run (once) (y) (enter)`, `Trust this workspace` |
| `grok` | xAI Grok CLI | `1. Yes` |
| `auggie` | Augment Code CLI | `Enable indexing` |
| `amp` | Sourcegraph Amp CLI | `Approve` |
| `qwen` | Alibaba Qwen Code | (reserved) |

```bash
# use with a specific AI CLI
auto-yes run --cli claude -- claude "fix the tests"
auto-yes --on --cli codex

# load all AI CLI profiles at once
auto-yes --on --cli all

# inspect patterns for a specific profile
auto-yes patterns claude codex
```

### Custom patterns

```bash
# persist a pattern across sessions
auto-yes add-pattern 'accept license\?'

# one-off extra pattern
auto-yes run --pattern 'custom_prompt\?' -- ./my-script.sh
```

### Adding a new AI CLI profile

Add a new entry to `REGISTRY` in `src/auto_yes/patterns.py`:

```python
_MY_TOOL = {
    "description": "My AI Tool CLI",
    "patterns": [
        (r"pattern_regex_here", None),    # respond with default
        (r"another_pattern", "yes"),      # respond with "yes"
    ],
}

REGISTRY["my-tool"] = _MY_TOOL
```

No other file needs to change.

## Configuration

Stored at `~/.config/auto-yes/config.json` (Linux/macOS) or
`%APPDATA%\auto-yes\config.json` (Windows):

```json
{
  "custom_patterns": [],
  "response": "y",
  "cooldown": 0.5,
  "verbose": false
}
```

## Platform support

| Platform | Method | Notes |
|----------|--------|-------|
| Linux | `pty` + `select` | Full PTY, zero external deps |
| macOS | `pty` + `select` | Full PTY, zero external deps |
| Windows | `pywinpty` | Install `auto-yes[windows]` |
| Windows (fallback) | `subprocess` pipes | Works but no true PTY |

## Comparison with `yes(1)`

| | `yes \| cmd` | `auto-yes run -- cmd` |
|---|---|---|
| Prompt detection | None (floods stdin) | Smart regex matching |
| User interaction | Impossible | Preserved |
| PTY | No (pipe) | Yes |
| Colours / progress bars | Often broken | Preserved |
| Cross-platform | Unix only | Unix + Windows |

## Python API

```python
from auto_yes.runner import Runner

# generic patterns only
runner = Runner(response="y", cooldown=0.5, verbose=True)
exit_code = runner.run_command(["apt", "install", "nginx"])

# with AI CLI profile
runner = Runner(categories=["generic", "claude"], verbose=True)
exit_code = runner.run_command(["claude", "fix the tests"])
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
