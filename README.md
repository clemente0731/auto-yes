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

### Wrap an AI CLI tool (recommended)

The simplest way: `auto-yes <profile> [args...]` wraps a tool in a single
process with auto-responses enabled and verbose output on by default:

```bash
auto-yes claude "fix the tests"        # runs: claude "fix the tests"
auto-yes cursor chat "fix the bug"     # runs: agent chat "fix the bug"
auto-yes aider --model gpt-4          # runs: aider --model gpt-4
auto-yes copilot                       # runs: gh copilot
auto-yes amazonq chat "help me"        # runs: q chat "help me"
```

The profile name is mapped to the real binary automatically (e.g. `cursor`
runs `agent`, `copilot` runs `gh copilot`).  Run `auto-yes list` to see all
available profiles and their real commands.

### Shell session mode

Start a persistent shell where every prompt is answered automatically:

```bash
auto-yes --on --cli claude
# you are now inside an auto-yes shell
exit                       # leave the session
```

### Single command mode

Wrap one command without entering a persistent session:

```bash
auto-yes run -- apt install nginx
auto-yes run --cli codex -- codex "fix tests"
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
auto-yes <profile> [ARGS...]       wrap an AI CLI tool directly (recommended)
auto-yes --on [OPTIONS]            start an auto-yes shell session
auto-yes run [OPTIONS] -- CMD...   run a single command with auto-yes
auto-yes list, -l, --list          list all available CLI profiles
auto-yes patterns [CATEGORY...]    list prompt patterns (optionally filtered)
auto-yes add-pattern PATTERN       persist a custom regex pattern
auto-yes del-pattern PATTERN       remove a custom pattern
auto-yes status                    check if auto-yes is active
auto-yes --off                     exit info
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
| Bracket choices | `[y/n]`, `[Y/n]`, `(y/N)`, `[yes/no]`, `([y]/n)`, `(y)` |
| Styled choices | `[Y]es / [N]o`, bare `y/n:` |
| Question sentences | `Continue?`, `Proceed?`, `Are you sure?`, `Would you like to…?` |
| Safe action prompts | `Allow?`, `Approve?`, `Accept?`, `Download?`, `Enable?`, `Create?` |
| Excluded (dangerous) | `Overwrite?`, `Delete?`, `Remove?`, `Upgrade?`, `Update?`, `Merge?`, `Restart?`, `Reboot?`, `Install?` (use `--pattern` to add manually) |
| Agreement prompts | `Do you agree?`, `Do you accept?`, `Accept the license`, `Agree to the terms` |
| Need/require prompts | `Need to install?`, `Required?`, `Necessary?` |
| Package managers | `Is this ok [y/d/N]` (pip excluded to avoid accidental uninstall) |
| SSH fingerprint | `continue connecting (yes/no/[fingerprint])?` → responds `yes` |
| Terraform | `Only 'yes' will be accepted` → responds `yes` |
| Full-word yes | `Type 'yes' to continue`, `Type 'YES' to confirm`, `Enter 'yes' to proceed` |
| Press enter/key | `Press Enter to continue`, `Press any key to continue` → responds with empty |
| Default value | `(default: Y)`, `[default=yes]` → responds with empty (accept default) |

### AI CLI profiles

| Profile | Command | Tool | Key patterns |
|---------|---------|------|-------------|
| `claude` | `claude` | Anthropic Claude Code | `1. Yes, I trust this folder`, `Yes, allow`, API key prompt |
| `gemini` | `gemini` | Google Gemini CLI | `1. Allow once`, `2. Allow for this session`, `3. Always allow` |
| `codex` | `codex` | OpenAI Codex CLI | `1. Approve and run now`, `1. Yes, allow Codex to work` |
| `copilot` | `gh copilot` | GitHub Copilot CLI | `1. Yes, proceed`, `Allow Copilot to run` |
| `cursor` | `agent` | Cursor Agent CLI | `→ Run (once) (y)`, `→ Run (always) (a)`, `Trust this workspace` |
| `grok` | `grok` | xAI Grok CLI | `1. Yes` |
| `auggie` | `auggie` | Augment Code CLI | `[Y] Enable indexing` |
| `amp` | `amp` | Sourcegraph Amp CLI | `Approve` |
| `aider` | `aider` | Aider AI Coding | `(Y)es/(N)o`, `Run shell command?`, `Add … to the chat?` |
| `openhands` | `openhands` | OpenHands AI Agent | `Do you want to execute this action?`, `Approve` |
| `windsurf` | `windsurf` | Codeium Windsurf | `Accept changes?`, `Run this command?` |
| `qwen` | `qwen` | Alibaba Qwen Code | `1. Yes`, `Approve execution?` |
| `amazonq` | `q` | Amazon Q Developer | `Do you approve this action?`, `Accept suggestion?` |

```bash
# recommended: wrap directly
auto-yes claude "fix the tests"
auto-yes cursor chat "fix the bug"

# advanced: explicit run mode
auto-yes run --cli codex -- codex "fix tests"
auto-yes --on --cli all

# inspect patterns for a specific profile
auto-yes patterns claude codex

# list all profiles and their real commands
auto-yes list
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
    "command": ["my-tool"],              # real binary name (list of strings)
    "patterns": [
        (r"pattern_regex_here", None),    # respond with default
        (r"another_pattern", "yes"),      # respond with "yes"
    ],
}

REGISTRY["my-tool"] = _MY_TOOL
```

The `command` field maps the profile name to the real binary.  For example,
the `cursor` profile has `"command": ["agent"]`, and `copilot` has
`"command": ["gh", "copilot"]`.  No other file needs to change.

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
from auto_yes.patterns import get_command

# generic patterns only
runner = Runner(response="y", cooldown=0.5, verbose=True)
exit_code = runner.run_command(["apt", "install", "nginx"])

# with AI CLI profile (using real binary name from registry)
runner = Runner(categories=["generic", "cursor"], verbose=True)
cmd = get_command("cursor")          # -> ["agent"]
exit_code = runner.run_command(cmd + ["chat", "fix the bug"])
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
