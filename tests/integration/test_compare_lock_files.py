import shutil
import tomllib
from collections.abc import Generator
from pathlib import Path

import orjson
import pytest
import rich

from uv_burn.main import main

ROOT_PATH = Path(__file__).parent / "test_case_data" / "compare_lock_files"
PIPFILE_PATH = ROOT_PATH / "Pipfile"
PIPFILE_LOCK_PATH = ROOT_PATH / "Pipfile.lock"
PYPROJECT_PATH = ROOT_PATH / "pyproject.toml"
UV_LOCK_PATH = ROOT_PATH / "uv.lock"


@pytest.fixture
def setup_and_teardown(tmp_path: Path) -> Generator[Path, None, None]:
    shutil.copy(PYPROJECT_PATH, tmp_path / "pyproject.toml")
    shutil.copy(UV_LOCK_PATH, tmp_path / "uv.lock")
    main(tmp_path)
    yield tmp_path
    for file in tmp_path.iterdir():
        file.unlink()


def test_compare_pipfiles(setup_and_teardown: Path) -> None:
    assert (setup_and_teardown / "Pipfile").exists()
    assert (setup_and_teardown / "Pipfile.lock").exists()

    with (setup_and_teardown / "Pipfile").open("rb") as f:
        created_pipfile_content = tomllib.load(f)

    with PIPFILE_PATH.open("rb") as f:
        expected_pipfile_content = tomllib.load(f)

    rich.print(created_pipfile_content)

    assert created_pipfile_content == expected_pipfile_content


def test_compare_lock_files(setup_and_teardown: Path) -> None:
    assert (setup_and_teardown / "Pipfile").exists()
    assert (setup_and_teardown / "Pipfile.lock").exists()

    with (setup_and_teardown / "Pipfile.lock").open("rb") as f:
        created_pipfile_lock_content = orjson.loads(f.read())

    with PIPFILE_LOCK_PATH.open("rb") as f:
        expected_pipfile_lock_content = orjson.loads(f.read())

    rich.print(created_pipfile_lock_content.keys())

    assert created_pipfile_lock_content == expected_pipfile_lock_content
