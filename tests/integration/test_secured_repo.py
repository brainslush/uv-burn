import os
from collections.abc import Generator
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from tests.integration.conftest import ProxyDetails
from uv_burn.main import _main

PATH_TO_TEST_PROJECT_ROOT = Path(__file__).parent / "test_case_data" / "secured_repo"


def _modify_pyproject_for_proxy(
    pyproject_source_path: Path, pyproject_target_path: Path, proxy_server: ProxyDetails
) -> None:
    content = pyproject_source_path.read_text()
    modified_content = content.replace(
        "http://127.0.0.1:8080/simple", f"http://{proxy_server.host}:{proxy_server.port}/simple"
    )
    pyproject_target_path.write_text(modified_content)


def _modify_uv_lock_for_proxy(uv_lock_source_path: Path, uv_lock_target_path: Path, proxy_server: ProxyDetails) -> None:
    content = uv_lock_source_path.read_text()
    modified_content = content.replace(
        "http://127.0.0.1:8080/simple", f"http://{proxy_server.host}:{proxy_server.port}/simple"
    )
    uv_lock_target_path.write_text(modified_content)


@pytest.fixture
def root_path(proxy_server: ProxyDetails, tmp_path: Path) -> Path:
    """Set up a temporary project directory with modified pyproject.toml and uv.lock."""

    pyproject_source_path = PATH_TO_TEST_PROJECT_ROOT / "pyproject.toml"
    modified_pyproject_path = tmp_path / "pyproject.toml"
    _modify_pyproject_for_proxy(pyproject_source_path, modified_pyproject_path, proxy_server)

    uv_lock_source_path = PATH_TO_TEST_PROJECT_ROOT / "uv.lock"
    modified_uv_lock_path = tmp_path / "uv.lock"
    _modify_uv_lock_for_proxy(uv_lock_source_path, modified_uv_lock_path, proxy_server)

    return tmp_path


@pytest.fixture
def set_env_vars() -> Generator[None]:
    """Set environment variables for secured repository access."""

    os.environ["UV_INDEX_SECURED_REPO_USERNAME"] = "userfoo"
    os.environ["UV_INDEX_SECURED_REPO_PASSWORD"] = "passbar"
    yield
    del os.environ["UV_INDEX_SECURED_REPO_USERNAME"]
    del os.environ["UV_INDEX_SECURED_REPO_PASSWORD"]


@pytest.mark.usefixtures("set_env_vars")
@pytest.mark.asyncio
async def test_can_convert_with_secure_index(
    mocker: MockerFixture, root_path: Path, proxy_server: ProxyDetails
) -> None:
    """Test that a secured repository can be accessed and converted."""

    await _main(
        root_path=root_path,
        pipfile_path=root_path / "Pipfile",
        pipfile_lock_path=root_path / "Pipfile.lock",
    )
