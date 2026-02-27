"""Command-line interface for auto-yes.

Usage (recommended)::

    auto-yes claude "fix tests"        wrap claude directly
    auto-yes cursor chat "fix bug"     wrap cursor agent CLI (runs ``agent``)
    auto-yes aider --model gpt-4      wrap aider with arguments
    auto-yes copilot                   wrap gh copilot

Usage (advanced)::

    auto-yes --on [OPTIONS]            start an auto-yes shell session
    auto-yes run [OPTIONS] -- CMD...   run a single command with auto-yes
    auto-yes list (-l, --list)         list all available CLI profiles
    auto-yes patterns [CATEGORY...]    list prompt patterns
    auto-yes add-pattern PATTERN       persist a custom pattern
    auto-yes del-pattern PATTERN       remove a custom pattern
"""

import argparse
import sys

from auto_yes import __version__
from auto_yes import config as _cfg
from auto_yes.patterns import (
    AI_CLI_NAMES,
    REGISTRY,
    available_categories,
    get_command,
    resolve_profile,
)
from auto_yes.runner import Runner

_PROG = "auto-yes"


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------


def _resolve_categories(cli_flags):
    """Turn the ``--cli`` flag values into a deduplicated category list.

    ``"all"`` expands to every registered category.
    ``"generic"`` is always included.
    """
    categories = ["generic"]

    for name in cli_flags or []:
        if name == "all":
            for key in REGISTRY:
                if key not in categories:
                    categories.append(key)
        elif name in REGISTRY:
            if name not in categories:
                categories.append(name)
        else:
            print(
                f"warning: unknown CLI profile '{name}', ignored.  "
                f"available: {', '.join(sorted(REGISTRY))}",
                file=sys.stderr,
            )

    return categories


def _build_runner(opts, cfg):
    """Create a ``Runner`` from parsed CLI flags merged with persistent cfg."""
    response = opts.response if opts.response is not None else cfg.get("response", "y")
    cooldown = opts.cooldown if opts.cooldown is not None else cfg.get("cooldown", 0.5)

    extra = list(cfg.get("custom_patterns", []))
    if hasattr(opts, "pattern") and opts.pattern:
        extra.extend(opts.pattern)

    cli_flags = getattr(opts, "cli", None) or []
    categories = _resolve_categories(cli_flags)

    return Runner(
        response=response,
        cooldown=cooldown,
        verbose=opts.verbose,
        categories=categories,
        extra_patterns=extra or None,
    )


def _make_opts_parser(prog):
    """Shared option flags for ``--on`` and ``run``."""
    parser = argparse.ArgumentParser(prog=prog, add_help=False)
    parser.add_argument("--response", default=None, help="text to send (default: y)")
    parser.add_argument(
        "--cooldown",
        type=float,
        default=None,
        help="seconds between auto-responses (default: 0.5)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="print a notice every time auto-yes responds",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        help="additional regex pattern (repeatable)",
    )
    parser.add_argument(
        "--cli",
        action="append",
        default=[],
        help=f"AI CLI profile to load (repeatable, or 'all').  "
        f"choices: {', '.join(AI_CLI_NAMES)}",
    )
    return parser


# ------------------------------------------------------------------
# sub-command handlers
# ------------------------------------------------------------------


def _handle_on(argv):
    parser = _make_opts_parser(f"{_PROG} --on")
    opts = parser.parse_args(argv)
    cfg = _cfg.load()
    runner = _build_runner(opts, cfg)

    response_display = opts.response or cfg.get("response", "y")
    loaded = _resolve_categories(opts.cli)
    print(
        f"\x1b[32m[auto-yes]\x1b[0m session started. "
        f"prompts will be auto-responded with '{response_display}'."
    )
    print(f"\x1b[32m[auto-yes]\x1b[0m loaded profiles: {', '.join(loaded)}")
    print("\x1b[32m[auto-yes]\x1b[0m type 'exit' to end the session.")

    code = runner.run_shell()

    print("\n\x1b[32m[auto-yes]\x1b[0m session ended.")
    sys.exit(code)


def _handle_off():
    if _is_active():
        print(
            "\x1b[32m[auto-yes]\x1b[0m you are inside an auto-yes session. " "type 'exit' to leave."
        )
    else:
        print("\x1b[32m[auto-yes]\x1b[0m auto-yes is not active.")


def _handle_status():
    if _is_active():
        print("auto-yes: \x1b[32mactive\x1b[0m")
    else:
        print("auto-yes: \x1b[90minactive\x1b[0m")


def _handle_run(argv):
    if "--" in argv:
        idx = argv.index("--")
        our_argv = argv[:idx]
        cmd_argv = argv[idx + 1 :]
    else:
        our_argv = []
        cmd_argv = argv

    if not cmd_argv:
        print("error: no command specified", file=sys.stderr)
        print(f"usage: {_PROG} run [OPTIONS] -- COMMAND...", file=sys.stderr)
        sys.exit(1)

    parser = _make_opts_parser(f"{_PROG} run")
    opts = parser.parse_args(our_argv)
    cfg = _cfg.load()
    runner = _build_runner(opts, cfg)

    code = runner.run_command(cmd_argv)
    sys.exit(code)


def _handle_patterns(argv):
    """List patterns, optionally filtered to specific categories."""
    cfg = _cfg.load()
    custom = cfg.get("custom_patterns", [])

    if argv:
        show_categories = argv
    else:
        show_categories = list(REGISTRY.keys())

    for name in show_categories:
        if name not in REGISTRY:
            print(f"unknown category: {name}", file=sys.stderr)
            continue

        entry = REGISTRY[name]
        pats = entry["patterns"]
        print(f"[{name}] {entry['description']} ({len(pats)})")
        if not pats:
            print("  (none)")
        for src, resp in pats:
            tag = f" -> '{resp}'" if resp is not None else ""
            print(f"  {src}{tag}")
        print()

    if custom:
        print(f"[custom] user-defined ({len(custom)})")
        for pat in custom:
            print(f"  {pat}")
        print()


def _handle_list():
    """List all available CLI profiles with description and pattern count."""
    print("available CLI profiles:\n")
    print(
        f"  {'PROFILE':<12s} {'COMMAND':<16s} "
        f"{'DESCRIPTION':<35s} {'PATTERNS':>8s}"
    )
    print(
        f"  {'-' * 12:<12s} {'-' * 16:<16s} "
        f"{'-' * 35:<35s} {'-' * 8:>8s}"
    )

    for name, desc in available_categories():
        count = len(REGISTRY[name]["patterns"])
        cmd = " ".join(get_command(name)) if name != "generic" else "-"
        marker = " (always loaded)" if name == "generic" else ""
        print(
            f"  {name:<12s} {cmd:<16s} "
            f"{desc:<35s} {count:>8d}{marker}"
        )

    total = sum(len(e["patterns"]) for e in REGISTRY.values())
    print(f"\n  {len(REGISTRY)} categories, {total} patterns total")
    print(
        "\ntip: run 'auto-yes <profile> [args...]' to wrap a tool directly "
        "(recommended)"
    )
    print("     e.g. auto-yes cursor chat 'fix the bug'")


def _handle_wrap(profile, argv):
    """Shorthand: ``auto-yes claude "fix tests"`` wraps the CLI tool directly.

    Equivalent to ``auto-yes run -v --cli <profile> -- <binary> <argv...>``.
    The real binary name is looked up from the REGISTRY ``command`` field.
    Verbose is on by default so users can see auto-yes in action.
    """
    cfg = _cfg.load()
    response = cfg.get("response", "y")
    cooldown = cfg.get("cooldown", 0.5)

    extra = list(cfg.get("custom_patterns", []))

    categories = _resolve_categories([profile])

    runner = Runner(
        response=response,
        cooldown=cooldown,
        verbose=True,
        categories=categories,
        extra_patterns=extra or None,
    )

    real_cmd = get_command(profile)

    if "--" in argv:
        idx = argv.index("--")
        cmd_argv = argv[idx + 1:]
    else:
        cmd_argv = real_cmd + list(argv)

    if not cmd_argv:
        cmd_argv = real_cmd

    cmd_display = " ".join(real_cmd)
    print(
        f"\x1b[32m[auto-yes]\x1b[0m wrapping '{cmd_display}' "
        f"with profile: generic, {profile}"
    )

    code = runner.run_command(cmd_argv)
    sys.exit(code)


def _handle_add_pattern(argv):
    if not argv:
        print("error: provide a regex pattern string", file=sys.stderr)
        sys.exit(1)
    pattern = argv[0]
    _cfg.add_pattern(pattern)
    print(f"added pattern: {pattern}")


def _handle_del_pattern(argv):
    if not argv:
        print("error: provide a regex pattern string", file=sys.stderr)
        sys.exit(1)
    pattern = argv[0]
    cfg = _cfg.remove_pattern(pattern)
    if pattern not in cfg.get("custom_patterns", []):
        print(f"removed pattern: {pattern}")
    else:
        print(f"pattern not found: {pattern}")


def _is_active():
    import os

    return os.environ.get("AUTO_YES_ACTIVE") == "1"


# ------------------------------------------------------------------
# help / banner
# ------------------------------------------------------------------

# retro-futuristic banner: bright→dim cyan for AUTO, bright→dim magenta for YES
_BANNER = (
    "\n"
    "  \x1b[96m▄▀█ █ █ ▀█▀ █▀█\x1b[0m  \x1b[90m//\x1b[0m  \x1b[95m█▄█ █▀▀ █▀\x1b[0m\n"
    "  \x1b[36m█▀█ █▄█  █  █▄█\x1b[0m  \x1b[90m//\x1b[0m  \x1b[35m █  ██▄ ▄█\x1b[0m\n"
    f"  \x1b[90m{'━' * 31}\x1b[0m\n"
    f"  \x1b[93mv{__version__}\x1b[0m \x1b[90m·\x1b[0m auto-respond to CLI prompts\n"
)

_HELP = f"""\
{_BANNER}
\x1b[97musage (recommended):\x1b[0m
  {_PROG} <profile> [ARGS...]       wrap an AI CLI tool directly (single process)

\x1b[97musage (advanced):\x1b[0m
  {_PROG} --on [OPTIONS]            start an auto-yes shell session (global)
  {_PROG} run [OPTIONS] -- CMD...   run a single command with auto-yes
  {_PROG} list, -l, --list          list all available CLI profiles
  {_PROG} patterns [CATEGORY...]    list prompt patterns
  {_PROG} add-pattern PATTERN       add a custom prompt pattern
  {_PROG} del-pattern PATTERN       remove a custom prompt pattern
  {_PROG} status                    check if auto-yes is active
  {_PROG} --off                     exit info

\x1b[97mavailable profiles:\x1b[0m {', '.join(AI_CLI_NAMES)}

\x1b[97moptions (for --on / run):\x1b[0m
  --response TEXT     text to send (default: y)
  --cooldown FLOAT    seconds between responses (default: 0.5)
  --verbose, -v       show when auto-yes responds
  --pattern REGEX     extra pattern (repeatable)
  --cli NAME          AI CLI profile to load (repeatable, or 'all')

\x1b[97mexamples:\x1b[0m
  \x1b[96m{_PROG} claude "fix the tests"\x1b[0m                 wrap claude (recommended)
  \x1b[96m{_PROG} cursor chat "fix the bug"\x1b[0m              wrap cursor agent CLI
  \x1b[96m{_PROG} aider --model gpt-4\x1b[0m                    wrap aider
  \x1b[96m{_PROG} copilot\x1b[0m                                wrap gh copilot
  \x1b[96m{_PROG} amazonq chat "help me"\x1b[0m                 wrap Amazon Q (q chat)
  \x1b[36m{_PROG} --on --cli all\x1b[0m                         global shell with all profiles
  \x1b[36m{_PROG} run --cli codex -- codex "fix tests"\x1b[0m   explicit run mode
  \x1b[36m{_PROG} list\x1b[0m                                   show all profiles
"""


# ------------------------------------------------------------------
# entry point
# ------------------------------------------------------------------


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in ("-h", "--help"):
        print(_HELP)
        return

    if argv[0] in ("--version", "-V"):
        print(f"{_PROG} {__version__}")
        return

    cmd = argv[0]
    rest = argv[1:]

    dispatch = {
        "--on": lambda: _handle_on(rest),
        "on": lambda: _handle_on(rest),
        "--off": _handle_off,
        "off": _handle_off,
        "status": _handle_status,
        "run": lambda: _handle_run(rest),
        "list": _handle_list,
        "-l": _handle_list,
        "--list": _handle_list,
        "patterns": lambda: _handle_patterns(rest),
        "add-pattern": lambda: _handle_add_pattern(rest),
        "del-pattern": lambda: _handle_del_pattern(rest),
    }

    handler = dispatch.get(cmd)
    if handler is not None:
        handler()
        return

    # if cmd matches a known AI CLI profile (by name or binary), use wrap mode
    profile = resolve_profile(cmd)
    if profile is not None:
        _handle_wrap(profile, rest)
        return

    print(f"unknown command: {cmd}", file=sys.stderr)
    print(_HELP, file=sys.stderr)
    sys.exit(1)
