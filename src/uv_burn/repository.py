import asyncio
import logging
import os
import re
from typing import NewType

from httpx import AsyncClient, BasicAuth
from pydantic import SecretStr
from pydantic_core import Url

from uv_burn.models.pyproject import Index, PyProject
from uv_burn.models.repository import PyPiSimpleResponse
from uv_burn.models.uv_lock import ExternalPackage

SENTINEL = None  # Sentinel value to indicate the end of the queue
LOGGER = logging.getLogger(__name__)
REGEX_NON_ALPHA = re.compile(r"[\W+]")


def find_auth(name: str) -> tuple[SecretStr, SecretStr] | None:
    """
    Finds authentication credentials for a given index name from environment variables.
    The environment variables should be named as follows:
    - UV_INDEX_{NAME}_USERNAME
    - UV_INDEX_{NAME}_PASSWORD
    where {NAME} is the uppercase version of the index name.
    Args:
        name (str): The name of the index.
    Returns:
        tuple[SecretStr, SecretStr] | None: A tuple containing the username and password as SecretStr,
        or None if the credentials are not found.
    """
    user = os.getenv(f"UV_INDEX_{re.sub(REGEX_NON_ALPHA, '_', name.upper())}_USERNAME", None)
    pw = os.getenv(f"UV_INDEX_{re.sub(REGEX_NON_ALPHA, '_', name.upper())}_PASSWORD", None)
    return (SecretStr(user), SecretStr(pw)) if user and pw else None


async def create_client(index_url: Url, auth: tuple[SecretStr, SecretStr] | None) -> AsyncClient:
    """
    Creates an asynchronous HTTP client for the given index URL with optional basic authentication.
    Args:
        index_url (Url): The base URL of the index.
        auth (tuple[SecretStr, SecretStr] | None): A tuple containing the username and password as SecretStr,
            or None if no authentication is needed.
    Returns:
        AsyncClient: An instance of AsyncClient configured with the base URL and authentication.
    """
    auth_method = BasicAuth(auth[0].get_secret_value(), auth[1].get_secret_value()) if auth else None
    return AsyncClient(
        base_url=index_url.unicode_string(), auth=auth_method, headers={"Accept": "application/vnd.pypi.simple.v1+json"}
    )


async def get_package_info(clients: dict[Url, AsyncClient], package: ExternalPackage) -> PyPiSimpleResponse:
    """
    Fetches package information from the appropriate index using the provided HTTP clients.
    Args:
        clients (dict[Url, AsyncClient]): A dictionary mapping index URLs to their corresponding AsyncClient instances.
        package (ExternalPackage): The package for which to fetch information.
    Returns:
        PyPiSimpleResponse: The parsed response containing package information.
    """

    client = clients[package.source.registry]
    response = await client.get(package.name, follow_redirects=True)
    response.raise_for_status()
    return PyPiSimpleResponse.model_validate(response.json())


PackageName = NewType("PackageName", str)


def get_indices_from_pyprojects(pyprojects: list[PyProject]) -> list[Index]:
    """
    Extracts unique indices from a list of packages.
    Args:
        pyprojects (list[PyProject]): A list of PyProject instances.
    Returns:
        list[Index]: A list of unique indices.
    """
    default_index = Index(name="pypi", url=Url("https://pypi.org/simple"))
    indices = [index for pp in pyprojects if pp.tool and pp.tool.uv for index in pp.tool.uv.indices]
    indices.append(default_index)
    return indices


async def get_required_python_versions_from_index(
    packages: list[ExternalPackage], indicies: list[Index]
) -> dict[PackageName, str]:
    """
    Fetches Python version markers for the specified packages from their respective indices.
    Args:
        packages (list[ExternalPackage]): A list of packages for which to fetch Python version markers.
        indicies (list[Index]): A list of indices where the packages are hosted.
    Returns:
        dict[str, str]: A dictionary mapping package names to their Python version markers.
    """

    clients: dict[Url, AsyncClient] = {}

    LOGGER.debug("Creating clients for indices: %s", [index.url for index in indicies])

    for index in indicies:
        auth = find_auth(index.name)
        clients[index.url] = await create_client(index.url, auth)

    LOGGER.debug("Clients created for indices %s:", list(clients.keys()))

    futures = [get_package_info(clients, pkg) for pkg in packages]
    results = await asyncio.gather(*futures)

    for client in clients.values():
        await client.aclose()

    package_version_markers: dict[PackageName, str] = {}
    for pkg, pkg_simple_info in zip(packages, results, strict=True):
        version_files = [
            file
            for file in pkg_simple_info.files
            if file.version == pkg.version and f"sha256:{file.hashes.sha256}" in pkg.hashes
        ]
        if not version_files:
            LOGGER.debug("Package info received: %s", pkg_simple_info)

            raise ValueError(f"Could not find file for {pkg.name}=={pkg.version} in index {pkg.source.registry}")

        version_markers = {requires_python for file in version_files if (requires_python := file.requires_python)}

        if not version_markers:
            continue

        if len(version_markers) > 1:
            raise ValueError(
                f"Multiple different requires-python markers found for {pkg.name}=={pkg.version} in index "
                f"{pkg.source.registry}: {version_markers}"
            )

        package_version_markers[PackageName(pkg.name)] = version_markers.pop()

    return package_version_markers
