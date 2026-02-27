"""Command-line interface for auto-yes.

Usage::

    auto-yes --on [OPTIONS]            start an auto-yes shell session
    auto-yes --off                     show how to exit the session
    auto-yes status                    check whether auto-yes is active
    auto-yes run [OPTIONS] -- CMD...   run a single command with auto-yes
    auto-yes patterns [CATEGORY...]    list prompt patterns
    auto-yes add-pattern PATTERN       persist a custom pattern
    auto-yes del-pattern PATTERN       remove a custom pattern
"""

import argparse
import sys

from auto_yes import __version__
from auto_yes import config as _cfg
from auto_yes.patterns import AI_CLI_NAMES, REGISTRY, available_categories
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

    for name in (cli_flags or []):
        if name == "all":
            for key in REGISTRY:
                if key not in categories:
                    categories.append(key)
        elif name in REGISTRY:
            if name not in categories:
                categories.append(name)
        else:
            print(
                "warning: unknown CLI profile '{}', ignored.  "
                "available: {}".format(name, ", ".join(sorted(REGISTRY))),
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
        "--cooldown", type=float, default=None,
        help="seconds between auto-responses (default: 0.5)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="print a notice every time auto-yes responds",
    )
    parser.add_argument(
        "--pattern", action="append", default=[],
        help="additional regex pattern (repeatable)",
    )
    parser.add_argument(
        "--cli", action="append", default=[],
        help="AI CLI profile to load (repeatable, or 'all').  "
             "choices: {}".format(", ".join(AI_CLI_NAMES)),
    )
    return parser


# ------------------------------------------------------------------
# sub-command handlers
# ------------------------------------------------------------------

def _handle_on(argv):
    parser = _make_opts_parser("{} --on".format(_PROG))
    opts = parser.parse_args(argv)
    cfg = _cfg.load()
    runner = _build_runner(opts, cfg)

    response_display = opts.response or cfg.get("response", "y")
    loaded = _resolve_categories(opts.cli)
    print(
        "\x1b[32m[auto-yes]\x1b[0m session started. "
        "prompts will be auto-responded with '{}'.".format(response_display)
    )
    print(
        "\x1b[32m[auto-yes]\x1b[0m loaded profiles: {}".format(
            ", ".join(loaded)
        )
    )
    print("\x1b[32m[auto-yes]\x1b[0m type 'exit' to end the session.")

    code = runner.run_shell()

    print("\n\x1b[32m[auto-yes]\x1b[0m session ended.")
    sys.exit(code)


def _handle_off():
    if _is_active():
        print(
            "\x1b[32m[auto-yes]\x1b[0m you are inside an auto-yes session. "
            "type 'exit' to leave."
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
        cmd_argv = argv[idx + 1:]
    else:
        our_argv = []
        cmd_argv = argv

    if not cmd_argv:
        print("error: no command specified", file=sys.stderr)
        print("usage: {} run [OPTIONS] -- COMMAND...".format(_PROG), file=sys.stderr)
        sys.exit(1)

    parser = _make_opts_parser("{} run".format(_PROG))
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
            print("unknown category: {}".format(name), file=sys.stderr)
            continue

        entry = REGISTRY[name]
        pats = entry["patterns"]
        print("[{}] {} ({})".format(name, entry["description"], len(pats)))
        if not pats:
            print("  (none)")
        for src, resp in pats:
            tag = " -> '{}'".format(resp) if resp is not None else ""
            print("  {}{}".format(src, tag))
        print()

    if custom:
        print("[custom] user-defined ({})".format(len(custom)))
        for pat in custom:
            print("  {}".format(pat))
        print()


def _handle_add_pattern(argv):
    if not argv:
        print("error: provide a regex pattern string", file=sys.stderr)
        sys.exit(1)
    pattern = argv[0]
    _cfg.add_pattern(pattern)
    print("added pattern: {}".format(pattern))


def _handle_del_pattern(argv):
    if not argv:
        print("error: provide a regex pattern string", file=sys.stderr)
        sys.exit(1)
    pattern = argv[0]
    cfg = _cfg.remove_pattern(pattern)
    if pattern not in cfg.get("custom_patterns", []):
        print("removed pattern: {}".format(pattern))
    else:
        print("pattern not found: {}".format(pattern))


def _is_active():
    import os
    return os.environ.get("AUTO_YES_ACTIVE") == "1"


# ------------------------------------------------------------------
# help
# ------------------------------------------------------------------

_HELP = """\
auto-yes v{version} - automatically respond 'yes' to CLI prompts

usage:
  {prog} --on [OPTIONS]            start an auto-yes shell session
  {prog} --off                     exit info
  {prog} status                    check if auto-yes is active
  {prog} run [OPTIONS] -- CMD...   run a single command with auto-yes
  {prog} patterns [CATEGORY...]    list prompt patterns (optionally filtered)
  {prog} add-pattern PATTERN       add a custom prompt pattern
  {prog} del-pattern PATTERN       remove a custom prompt pattern

options (for --on / run):
  --response TEXT     text to send (default: y)
  --cooldown FLOAT    seconds between responses (default: 0.5)
  --verbose, -v       show when auto-yes responds
  --pattern REGEX     extra pattern (repeatable)
  --cli NAME          AI CLI profile to load (repeatable, or 'all')
                      choices: {cli_names}

examples:
  {prog} --on                                   enter an auto-yes shell
  {prog} --on --cli claude                      with Claude patterns
  {prog} --on --cli all                         with all AI CLI patterns
  {prog} run --cli codex -- codex "fix tests"   wrap Codex CLI
  {prog} run -v -- pip install flask             verbose single command
  {prog} patterns claude codex                  show specific categories
  {prog} add-pattern 'accept\\?'                add custom pattern
""".format(version=__version__, prog=_PROG, cli_names=", ".join(AI_CLI_NAMES))


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
        print("{} {}".format(_PROG, __version__))
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
        "patterns": lambda: _handle_patterns(rest),
        "add-pattern": lambda: _handle_add_pattern(rest),
        "del-pattern": lambda: _handle_del_pattern(rest),
    }

    handler = dispatch.get(cmd)
    if handler is None:
        print("unknown command: {}".format(cmd), file=sys.stderr)
        print(_HELP, file=sys.stderr)
        sys.exit(1)

    handler()
