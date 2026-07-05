#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block obviously destructive shell commands.

This is a best-effort denylist speed bump, not a sandbox — it does not parse
shell semantics, so obfuscated commands (variable expansion, base64, $(...),
alternate binaries) can bypass it. It fails open (exit 0) on any input it
cannot parse, so a bug here must never block every tool call.
"""
import json
import re
import sys

DESTRUCTIVE_PATTERNS = [
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+(/|~)(\s|$)"), "recursive force-delete of / or ~"),
    (re.compile(r"\bmkfs(\.\w+)?\b"), "filesystem creation (mkfs)"),
    (re.compile(r"\bdd\s+.*\bof=/dev/"), "raw write to a /dev block device"),
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&?\s*\}\s*;\s*:"), "shell fork bomb"),
    (re.compile(r"\bchmod\s+-R\s+777\s+/(\s|$)"), "recursive chmod 777 on /"),
]


def main():
    try:
        payload = json.load(sys.stdin)
        command = payload["tool_input"]["command"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return 0

    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            print(f"Blocked: command matches destructive pattern ({reason}).", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
