import logging
from asyncio import run as aiorun
from pathlib import Path
from typing import Annotated

import typer
from rich.logging import RichHandler

from uv_burn.models.uv_lock import ExternalPackage
from uv_burn.repository import get_indices_from_pyprojects, get_required_python_versions_from_index

from .convert import convert_pyprojects_to_pipfile, convert_uv_lock_to_pipfile_lock
from .io import (
    compute_pipfile_hash,
    find_pyproject_files,
    find_uv_lock_file,
    load_files,
    save_pipfile,
    save_pipfile_lock,
)

LOGGER = logging.getLogger(__name__)


def _setup_logging(level: str | int) -> None:
    logging.basicConfig(handlers=[RichHandler()], level=level)


async def _main(
    root_path: Path,
    pipfile_path: Path,
    pipfile_lock_path: Path,
) -> None:
    pyproject_files = find_pyproject_files(root_path)
    uv_lock_file = find_uv_lock_file(root_path)

    if not pyproject_files:
        typer.echo("No pyproject.toml files found.")
        raise typer.Exit(code=1)
    if not uv_lock_file:
        typer.echo("No uv.lock file found.")
        raise typer.Exit(code=1)

    pyprojects, uv_lock = load_files(pyproject_files, uv_lock_file)
    pipfile, source_url_name_map = convert_pyprojects_to_pipfile(pyprojects)
    save_pipfile(pipfile, pipfile_path)
    hash_pipfile = compute_pipfile_hash(pipfile)

    required_python_versions = await get_required_python_versions_from_index(
        uv_lock.packages_by_type(ExternalPackage),
        get_indices_from_pyprojects(pyprojects),
    )
    pipfile_lock = convert_uv_lock_to_pipfile_lock(uv_lock, hash_pipfile, source_url_name_map, required_python_versions)
    hash_pipfile_lock = save_pipfile_lock(pipfile_lock, pipfile_lock_path)

    typer.echo(f"Converted {len(pyproject_files)} pyproject.toml files and {uv_lock_file} to Pipfile and Pipfile.lock.")
    typer.echo(f"Pipfile saved to {pipfile_path} with hash {hash_pipfile}.")
    typer.echo(f"Pipfile.lock saved to {pipfile_lock_path} with hash {hash_pipfile_lock}.")


def main(
    root_path: Path,
    output_path: Annotated[
        Path | None,
        typer.Option(..., "--output", "-o", help="Path to the target directory where pipenv files will be created."),
    ] = None,
    force: Annotated[  # noqa: FBT002
        bool, typer.Option(..., "--force", "-f", help="Overwrite existing Pipfile and Pipfile.lock files.")
    ] = False,
    verbose: Annotated[bool, typer.Option(..., "--verbose", "-v", help="Enable verbose logging.")] = False,  # noqa: FBT002
) -> None:
    """
    Convert pyproject.toml and uv.lock files to Pipfile and Pipfile.lock.
    This script searches for pyproject.toml files in the specified root directory and its subdirectories,
    and converts them along with a uv.lock file into Pipfile and Pipfile.lock files.
    The output files are saved in the specified output directory.
    If the output directory is not specified, the files are saved in the root directory.
    If the Pipfile or Pipfile.lock already exists, it will raise an error unless --force is used.
    """

    log_level = logging.DEBUG if verbose else logging.INFO
    _setup_logging(log_level)

    if not root_path.is_dir():
        typer.echo(f"Error: {root_path} is not a valid directory.")
        raise typer.Exit(code=1)
    if output_path is None:
        output_path = root_path
    if not output_path.is_dir():
        typer.echo(f"Error: {output_path} is not a valid directory.")
        raise typer.Exit(code=1)

    pipfile_path = output_path / "Pipfile"
    pipfile_lock_path = output_path / "Pipfile.lock"

    if pipfile_path.exists() and not force:
        typer.echo(f"Error: {pipfile_path} already exists. Use --force or -f to overwrite it.")
        raise typer.Exit(code=1)
    if pipfile_lock_path.exists() and not force:
        typer.echo(f"Error: {pipfile_lock_path} already exists. Use --force or -f to overwrite it.")
        raise typer.Exit(code=1)

    aiorun(_main(root_path=root_path, pipfile_path=pipfile_path, pipfile_lock_path=pipfile_lock_path))


def cli() -> None:
    """
    CLI entry point for the script.
    """
    typer.run(main)
