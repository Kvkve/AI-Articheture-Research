#!/usr/bin/env python3
"""Claude Code "Stop" hook: run every check before the main agent ends its turn.

Claude Code passes a JSON object on standard input. Exit codes (from
https://code.claude.com/docs/en/hooks, read 2026-11-24):
0 lets the agent end; 2 keeps the agent working and gives it our standard
error text; any other non-zero code is shown to the user and does not block.
Uses the standard library only, so it runs before any dependency is installed.
"""

import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
CHECK_COMMAND = [str(REPOSITORY_ROOT / "scripts" / "check.sh")]

# Claude Code caps the text it gives to the agent at 10,000 characters.
# Staying well under the cap keeps our own heading and the end of the output
# (where the failed step is named) from being cut off.
MAX_MESSAGE_CHARACTERS = 8000

EXIT_ALLOW_STOP = 0
EXIT_SHOW_TO_USER = 1
EXIT_BLOCK_STOP = 2


def read_stop_hook_active(input_text: str) -> bool:
    """Return the stop_hook_active flag. Missing or broken input counts as false."""
    try:
        data = json.loads(input_text)
    except json.JSONDecodeError:
        return False
    if not isinstance(data, dict):
        return False
    return data.get("stop_hook_active") is True


def run_checks(command: list[str]) -> tuple[int, str]:
    """Run the check command and return its exit code and output.

    Standard error goes into the same stream as standard output, so the text
    stays in the order it was written and the failed step stays last.
    """
    try:
        # The command is fixed in this file or given by a test, never taken from input.
        result = subprocess.run(  # noqa: S603
            command,
            cwd=REPOSITORY_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    except OSError as error:
        # If the checks cannot even start, the gate must stay closed.
        # Letting the agent stop here would mean stopping with no checks run.
        return 1, f"The check command could not be started: {error}\n"
    return result.returncode, result.stdout


def build_message(check_output: str) -> str:
    """Return a heading plus the end of the check output, within the size limit."""
    # The hook runs at the end of every turn, and a failure may be expected.
    # So the heading tells the agent what to do, not only what happened.
    heading = (
        "scripts/check.sh failed. Fix the cause if it is yours to fix. "
        "If the checks cannot pass honestly, or the failure is expected, "
        "do not edit tests, check settings or the owner's code to get a pass: "
        "stop and explain. The end of the output:\n"
    )
    room_for_output = MAX_MESSAGE_CHARACTERS - len(heading)
    return heading + check_output[-room_for_output:]


def main(input_text: str, command: list[str]) -> int:
    exit_code, output = run_checks(command)
    if exit_code == 0:
        return EXIT_ALLOW_STOP

    sys.stderr.write(build_message(output))
    if read_stop_hook_active(input_text):
        # The agent has already had one chance to fix the checks.
        # Blocking again could loop forever, and the project rule is to stop
        # and explain when the checks cannot pass honestly. So we only report.
        return EXIT_SHOW_TO_USER
    return EXIT_BLOCK_STOP


if __name__ == "__main__":
    sys.exit(main(sys.stdin.read(), CHECK_COMMAND))
