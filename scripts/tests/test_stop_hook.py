import sys

import pytest

from stop_hook import MAX_MESSAGE_CHARACTERS, main

# Fake check commands, so the tests do not run the real checks.
PASSING_CHECK = [sys.executable, "-c", "print('all checks passed')"]
FAILING_CHECK = [
    sys.executable,
    "-c",
    "print('step failed: ruff'); raise SystemExit(1)",
]
LONG_FAILING_CHECK = [
    sys.executable,
    "-c",
    "print('x' * 20000); print('step failed: pytest'); raise SystemExit(1)",
]


def test_passing_checks_allow_stop_and_print_nothing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main('{"stop_hook_active": false}', PASSING_CHECK)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_failing_checks_block_stop_on_first_try(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main('{"stop_hook_active": false}', FAILING_CHECK)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "step failed: ruff" in captured.err


def test_failing_checks_do_not_block_again_when_hook_is_active(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main('{"stop_hook_active": true}', FAILING_CHECK)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "step failed: ruff" in captured.err


@pytest.mark.parametrize("input_text", ["", "not json", "[1, 2]", '{"other": 1}'])
def test_missing_or_invalid_input_counts_as_first_try(
    input_text: str, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(input_text, FAILING_CHECK)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "step failed: ruff" in captured.err


def test_long_output_is_cut_to_its_end(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main('{"stop_hook_active": false}', LONG_FAILING_CHECK)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert len(captured.err) <= MAX_MESSAGE_CHARACTERS
    assert captured.err.rstrip().endswith("step failed: pytest")
