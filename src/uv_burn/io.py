import json
import tomllib
from hashlib import sha256
from pathlib import Path
from typing import NewType

import tomli_w

from uv_burn.models.pipenv import MetaHash, Pipfile, PipfileHash
from uv_burn.models.pipenv_lock import PipfileLock
from uv_burn.models.pyproject import PyProject
from uv_burn.models.uv_lock import UvLock


def find_pyproject_files(root: Path) -> list[Path]:
    """
    Find all pyproject.toml files in the given directory and its subdirectories.

    Args:
        root (Path): The root directory to search in.

    Returns:
        list[Path]: A list of Paths to the found pyproject.toml files.
    """
    return list(root.rglob("pyproject.toml"))


def find_uv_lock_file(root: Path) -> Path | None:
    """
    Find the uv.lock file in the given directory and its subdirectories.

    Args:
        root (Path): The root directory to search in.

    Returns:
        Path | None: The path to the found uv.lock file, or None if not found.
    """
    uv_lock_files = list(root.rglob("uv.lock"))
    if uv_lock_files:
        return uv_lock_files[0]
    return None


def load_files(pyproject_files: list[Path], uv_lock_file: Path) -> tuple[list[PyProject], UvLock]:
    """
    Load the pyproject.toml and uv.lock files from the specified paths.

    Args:
        pyproject_files (list[Path]): List of paths to pyproject.toml files.
        uv_lock_file (Path): Path to the uv.lock file.
        target_path (Path): Path to the target directory.

    Returns:
        SourceModels: An instance containing the loaded PyProject and UvTool models.
    """
    if not pyproject_files:
        raise FileNotFoundError("No pyproject.toml files found.")

    pyprojects = []
    for pyproject_file in pyproject_files:
        with pyproject_file.open("rb") as f:
            pyproject_data = tomllib.load(f)
            pyprojects.append(PyProject.model_validate(pyproject_data))

    with uv_lock_file.open("rb") as f:
        uv_lock_data = tomllib.load(f)
        uv_lock = UvLock.model_validate(uv_lock_data)

    return pyprojects, uv_lock


Hash = NewType("Hash", str)


def save_pipfile(pipfile: Pipfile, pipfile_path: Path) -> None:
    """
    Save the Pipfile to the specified target path.

    Args:
        pipfile (Pipfile): The Pipfile model to save.
        pipfile_path (Path): The path to the Pipfile to save.
    """
    toml = tomli_w.dumps(pipfile.model_dump(mode="json", exclude_none=True))
    pipfile_path.write_text(toml)


def compute_pipfile_hash(pipfile: Pipfile) -> Hash:
    """
    Compute the SHA-256 hash of the Pipfile content.
    Args:
        pipfile (Pipfile): The Pipfile model to compute the hash for.
    Returns:
        Hash: The SHA-256 hash of the Pipfile content.
    """

    meta = MetaHash(sources=pipfile.sources, requires=pipfile.requires)
    pipfile_hash = PipfileHash(meta=meta, default=pipfile.packages, develop=pipfile.dev_packages)

    pipfile_hash_json = pipfile_hash.model_dump(mode="json", by_alias=True)
    json_text = json.dumps(pipfile_hash_json, sort_keys=True, separators=(",", ":"))
    json_bytes = json_text.encode("utf-8")
    return Hash(sha256(json_bytes).hexdigest())


def save_pipfile_lock(pipfile_lock: PipfileLock, pipfile_lock_path: Path) -> None:
    """
    Save the Pipfile.lock to the specified target path.

    Args:
        pipfile_lock (PipfileLock): The PipfileLock model to save.
        pipfile_lock_path (Path): The path to the Pipfile.lock to save.
    """
    pipfile_lock_path.write_text(pipfile_lock.model_dump_json(indent=4, by_alias=True))
