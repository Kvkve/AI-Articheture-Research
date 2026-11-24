#!/usr/bin/env python3
"""Check that every path in backticks in docs/architecture.md exists.

The file shows only what is built, so there is no "created at first use" exception.
Text in fenced code blocks, such as the Mermaid diagram, is not read.
Uses the standard library only, so it runs before any dependency is installed.
"""

import re
import sys
from pathlib import Path

ARCHITECTURE_FILE = "docs/architecture.md"
FENCE_START = "```"
API_ADDRESS_START = "/"
BACKTICK_TEXT = re.compile(r"`([^`]+)`")


def find_backtick_texts(architecture_text: str) -> list[str]:
    """Return every text in single backticks that is outside fenced code blocks."""
    texts: list[str] = []
    inside_fence = False
    for line in architecture_text.splitlines():
        if line.startswith(FENCE_START):
            inside_fence = not inside_fence
            continue
        if not inside_fence:
            texts.extend(BACKTICK_TEXT.findall(line))
    return texts


def find_problems(architecture_text: str, root: Path) -> list[str]:
    """Return one message per problem. An empty list means every path exists."""
    problems: list[str] = []
    for path_text in find_backtick_texts(architecture_text):
        # Text that starts with "/" is an address of the backend API, not a file.
        if path_text.startswith(API_ADDRESS_START):
            continue
        path = root / path_text
        if path_text.endswith("/"):
            if path.is_dir():
                continue
            if path.exists():
                problems.append(f"Not a directory: {path_text}")
                continue
        elif path.exists():
            continue
        problems.append(f"Missing path: {path_text}")
    return problems


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    architecture_text = (root / ARCHITECTURE_FILE).read_text(encoding="utf-8")
    problems = find_problems(architecture_text, root)
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print("Every path in docs/architecture.md exists.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
