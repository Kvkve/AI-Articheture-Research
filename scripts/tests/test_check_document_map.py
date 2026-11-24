from pathlib import Path

from check_document_map import find_problems

TABLE_HEAD = """# Project rules

## Document map

| When | Read | What it holds |
|---|---|---|
"""

TABLE_TAIL = """
## Next section

Text that names `not/a/map/path.md` and must be ignored.
"""


def make_agents_text(*rows: str) -> str:
    return TABLE_HEAD + "\n".join(rows) + "\n" + TABLE_TAIL


def test_all_paths_exist_passes(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "status.md").write_text("status")
    (tmp_path / "README.md").write_text("readme")
    text = make_agents_text(
        "| Starting | `docs/status.md` | Status |",
        "| Background | `README.md` | Background, see `docs/` |",
    )

    assert find_problems(text, tmp_path) == []


def test_missing_path_without_marker_fails_and_names_path(tmp_path: Path) -> None:
    text = make_agents_text("| Starting | `docs/status.md` | Status |")

    problems = find_problems(text, tmp_path)

    assert len(problems) == 1
    assert "docs/status.md" in problems[0]


def test_missing_path_with_marker_passes(tmp_path: Path) -> None:
    text = make_agents_text(
        "| Borrowing | `docs/sources.md` | Sources (created at first use) |",
        "| Learning | `docs/learning/` | Notes (created at first use) |",
    )

    assert find_problems(text, tmp_path) == []


def test_no_table_fails(tmp_path: Path) -> None:
    text = "# Project rules\n\n## Document map\n\nNo table here.\n"

    assert find_problems(text, tmp_path) != []


def test_no_section_fails(tmp_path: Path) -> None:
    text = "# Project rules\n\n| When | Read |\n|---|---|\n| Start | `README.md` |\n"
    (tmp_path / "README.md").write_text("readme")

    assert find_problems(text, tmp_path) != []


def test_path_ending_in_slash_that_is_a_file_fails(tmp_path: Path) -> None:
    (tmp_path / "docs").write_text("a file, not a folder")
    text = make_agents_text("| Docs | `docs/` | All documents |")

    problems = find_problems(text, tmp_path)

    assert len(problems) == 1
    assert "docs/" in problems[0]


def test_path_ending_in_slash_that_is_a_file_fails_even_with_marker(
    tmp_path: Path,
) -> None:
    (tmp_path / "learning").write_text("a file, not a folder")
    text = make_agents_text("| Learning | `learning/` | Notes (created at first use) |")

    assert find_problems(text, tmp_path) != []


def test_marker_only_allows_the_path_in_its_own_row(tmp_path: Path) -> None:
    text = make_agents_text(
        "| Starting | `docs/status.md` | Status |",
        "| Borrowing | `docs/sources.md` | Sources (created at first use) |",
    )

    problems = find_problems(text, tmp_path)

    assert len(problems) == 1
    assert "docs/status.md" in problems[0]
