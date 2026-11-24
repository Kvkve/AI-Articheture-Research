#!/usr/bin/env python3
"""Check that every path named in the document map of AGENTS.md exists.

A path may be missing only when its row says "created at first use".
Uses the standard library only, so it runs before any dependency is installed.
"""

import re
import sys
from pathlib import Path

SECTION_HEADING = "## Document map"
FIRST_USE_MARKER = "created at first use"
BACKTICK_TEXT = re.compile(r"`([^`]+)`")
SEPARATOR_ROW = re.compile(r"^\|[\s:|-]+\|$")


def find_table_rows(agents_text: str) -> list[str]:
    """Return the body rows of the first table in the document map section."""
    lines = agents_text.splitlines()
    try:
        start = lines.index(SECTION_HEADING)
    except ValueError:
        return []

    table_lines: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("#"):
            break
        if stripped.startswith("|"):
            table_lines.append(stripped)
        elif table_lines:
            # A non-table line after the table means the table has ended.
            break

    # The first two lines are the header row and the separator row.
    if len(table_lines) < 2 or not SEPARATOR_ROW.match(table_lines[1]):
        return []
    return table_lines[2:]


def find_problems(agents_text: str, root: Path) -> list[str]:
    """Return one message per problem. An empty list means the map is correct."""
    rows = find_table_rows(agents_text)
    if not rows:
        return [f"No table rows found under '{SECTION_HEADING}'."]

    problems: list[str] = []
    for row in rows:
        allowed_missing = FIRST_USE_MARKER in row
        for path_text in BACKTICK_TEXT.findall(row):
            path = root / path_text
            if path_text.endswith("/"):
                if path.is_dir():
                    continue
                if path.exists():
                    problems.append(f"Not a directory: {path_text}")
                    continue
            elif path.exists():
                continue
            if not allowed_missing:
                problems.append(f"Missing path: {path_text}")
    return problems


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
    problems = find_problems(agents_text, root)
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print("Document map is correct.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
