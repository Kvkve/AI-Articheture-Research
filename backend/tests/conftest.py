from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def database_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Every test gets its own database file in a temporary folder, so no test
    # can write to the default database file. The folder "data" does not
    # exist yet, which also tests that it is made when needed.
    path = tmp_path / "data" / "app.db"
    monkeypatch.setenv("POC_DATABASE_FILE", str(path))
    return path
