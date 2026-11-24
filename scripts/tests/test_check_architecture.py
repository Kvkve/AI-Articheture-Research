from pathlib import Path

from check_architecture import find_problems


def test_all_paths_exist_passes(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "tasks.md").write_text("tasks")
    (tmp_path / "README.md").write_text("readme")
    text = "Target: `README.md`. Plan: `docs/tasks.md`, see `docs/`.\n"

    assert find_problems(text, tmp_path) == []


def test_missing_path_fails_and_names_path(tmp_path: Path) -> None:
    text = "| Backend API | `backend/app/main.py` | Answers requests. |\n"

    problems = find_problems(text, tmp_path)

    assert len(problems) == 1
    assert "backend/app/main.py" in problems[0]


def test_only_the_missing_path_on_a_line_is_reported(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "check.sh").write_text("checks")
    (tmp_path / "README.md").write_text("readme")
    text = "| Checks | `scripts/check.sh`, `scripts/gone.py`, `README.md` | Runs. |\n"

    problems = find_problems(text, tmp_path)

    assert len(problems) == 1
    assert "scripts/gone.py" in problems[0]


def test_api_address_is_not_reported(tmp_path: Path) -> None:
    text = "Today it has one endpoint, `/health`.\n"

    assert find_problems(text, tmp_path) == []


def test_fenced_code_block_is_skipped_and_text_after_it_is_checked(
    tmp_path: Path,
) -> None:
    text = (
        "```mermaid\n"
        "flowchart TB\n"
        '    A["`inside/the/diagram.py`"]\n'
        "```\n"
        "\n"
        "After the diagram: `after/the/diagram.py`.\n"
    )

    problems = find_problems(text, tmp_path)

    assert len(problems) == 1
    assert "after/the/diagram.py" in problems[0]


def test_path_ending_in_slash_that_is_a_file_fails(tmp_path: Path) -> None:
    (tmp_path / "frontend").write_text("a file, not a folder")
    text = "The checks look at `frontend/`.\n"

    problems = find_problems(text, tmp_path)

    assert len(problems) == 1
    assert "frontend/" in problems[0]


def test_unclosed_fenced_code_block_fails(tmp_path: Path) -> None:
    text = "```mermaid\nflowchart TB\n\nAfter the diagram: `after/the/diagram.py`.\n"

    problems = find_problems(text, tmp_path)

    assert len(problems) == 1
    assert "never closed" in problems[0]


def test_missing_folder_fails_and_names_path(tmp_path: Path) -> None:
    text = "The tests are in `backend/tests/`.\n"

    problems = find_problems(text, tmp_path)

    assert len(problems) == 1
    assert "backend/tests/" in problems[0]
