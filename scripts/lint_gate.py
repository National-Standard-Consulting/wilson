#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""NAT-475 verify gate: fail only on NEW ruff findings on changed lines.

The repo baseline is large by design (recorded in state_ledger.md); the
enforceable rule is "your diff introduces no new findings". This script:

  1. Runs `ruff check --output-format=json` over the files touched by the diff.
  2. Parses `git diff -U0 <base>` into a per-file set of added line numbers.
  3. Reports a finding only when its line is in the added set.

Exit 0 = clean, 1 = new findings, 2 = usage/environment error.

Usage: scripts/lint_gate.py <base-ref>   (e.g. origin/main)
"""
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def changed_lines(base_ref: str) -> dict[str, set[int]]:
    """Per-file set of ADDED line numbers from a -U0 unified diff."""
    out = subprocess.run(
        ["git", "diff", "-U0", "--no-color", base_ref, "--", "*.py"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    result: dict[str, set[int]] = defaultdict(set)
    current: str | None = None
    # Old side is "\d+(,\d+)?" — NOT \S+: a new file's hunk header is
    # "-0,0 +1,6 @@", and \S+ swallows "-0,0" then demands "+" at the wrong
    # offset, matching nothing. First probe of this gate caught it (NAT-475):
    # a new file with two F401s read as "clean".
    hunk = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            result.setdefault(current, set())
        elif line.startswith("@@"):
            m = hunk.match(line)
            if not m or current is None:
                current = None
                continue
            start = int(m.group(1))
            count = int(m.group(2) or "1")
            if current is not None and count:
                result[current].update(range(start, start + count))
        elif line.startswith("--- "):
            current = None
    return {f: lines for f, lines in result.items() if lines}


def ruff_findings(files: list[str]) -> list[dict]:
    if not files:
        return []
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--output-format=json", *files],
        cwd=REPO, capture_output=True, text=True,
    )
    # ruff exits 1 when findings exist; that is data, not failure.
    if proc.returncode not in (0, 1):
        print(proc.stderr, file=sys.stderr)
        sys.exit(2)
    return json.loads(proc.stdout or "[]")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    base_ref = sys.argv[1]
    diff = changed_lines(base_ref)
    findings = ruff_findings(sorted(diff))
    # ruff reports absolute paths; make them repo-relative. NOT lstrip("./"):
    # lstrip strips a CHARACTER SET, so "/home/chris/..." became
    # "home/chris/..." and never matched a diff key -- the first probes of
    # this gate read "clean" on a file with two F401s (NAT-475).
    def rel(filename: str) -> str:
        try:
            return str(Path(filename).resolve().relative_to(REPO))
        except ValueError:
            return filename
    new = [
        f for f in findings
        if rel(f["filename"]) in diff
        and f["location"]["row"] in diff[rel(f["filename"])]
    ]
    if not new:
        print(f"lint gate: clean ({sum(len(v) for v in diff.values())} added lines checked)")
        return 0
    for f in sorted(new, key=lambda x: (x["filename"], x["location"]["row"])):
        print(f"{rel(f['filename'])}:{f['location']['row']}: {f['code']} {f['message']}")
    print(f"\nlint gate: {len(new)} NEW finding(s) on changed lines (NAT-475).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
