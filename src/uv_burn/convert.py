from collections import defaultdict

from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from pydantic_core import Url

from .models import (
    ExternalPackage,
    InternalPackage,
    LockHash,
    LockMeta,
    LockMetaRequires,
    LockMetaSource,
    LockPackageEntry,
    PackageDefinition,
    PackageGit,
    Pipfile,
    PipfileLock,
    PipfilePackage,
    PipfileRequires,
    PipfileSource,
    PyProject,
    UvLock,
)
from .repository import PackageName


def convert_pyprojects_to_pipfile(pyprojects: list[PyProject]) -> tuple[Pipfile, dict[Url, str]]:
    """
    Convert a list of PyProject objects and a UvLock object to a Pipfile and a mapping of source URLs to names.
    """

    sources: list[PipfileSource] = [
        PipfileSource(
            name="pypi",
            url=Url("https://pypi.org/simple"),
            verify_ssl=True,
        )
    ]
    packages: dict[str, str | PipfilePackage] = {}

    for pyproject in pyprojects:
        if pyproject.tool and pyproject.tool.uv:
            sources.extend(
                [
                    PipfileSource(
                        name=index.name,
                        url=index.url,
                        verify_ssl=True,
                    )
                    for index in pyproject.tool.uv.indices
                ]
            )
        for dep in pyproject.project.dependencies:
            req = Requirement(dep)
            match req:
                case Requirement(name=name, specifier=specifier, marker=None, url=None):
                    packages[name] = str(specifier)
                case Requirement(name=name, specifier=specifier, marker=marker, extras=extras, url=None):
                    packages[name] = PackageDefinition(
                        version=str(specifier),
                        markers=str(marker) if marker else None,
                        extras=list(extras) if extras else None,
                    )
                case Requirement(name=name, specifier=specifier, marker=marker, extras=extras, url=url):
                    packages[name] = PackageGit(url=str(url), markers=str(marker) if marker else None)

    source_url_name_map = {source.url: source.name for source in sources}
    python_version = Specifier(pyprojects[0].project.requires_python).version

    return (
        Pipfile(sources=sources, packages=packages, requires=PipfileRequires(python_version=python_version)),
        source_url_name_map,
    )


def convert_uv_lock_to_pipfile_lock(
    uv_lock: UvLock,
    pipfile_hash: str,
    source_url_name_map: dict[Url, str],
    required_python_versions: dict[PackageName, str],
) -> PipfileLock:
    """
    Convert a UvLock object to a PipfileLock object.
    """

    default_packages: dict[str, LockPackageEntry] = {}

    markers: defaultdict[str, list[str]] = defaultdict(list)
    for package in uv_lock.packages:
        if isinstance(package, InternalPackage):
            continue
        for dep in package.dependencies:
            if dep.marker:
                markers[dep.name].append(dep.marker)

    for package in uv_lock.packages:
        if not isinstance(package, ExternalPackage):
            continue

        hashes: list[str] = []
        hashes.extend([wheel.hash for wheel in package.wheels])
        if package.sdist and package.sdist.hash:
            hashes.append(package.sdist.hash)

        required_python = required_python_versions.get(PackageName(package.name), uv_lock.requires_python)
        python_specifiers = SpecifierSet(required_python)
        python_specifiers_pipenv_format = ", ".join([f"{s.operator} '{s.version}'" for s in python_specifiers])

        required_python_marker = f"python_version {python_specifiers_pipenv_format}"

        default_packages[package.name] = LockPackageEntry(
            version=f"=={package.version}",
            hashes=hashes,
            index=source_url_name_map[package.source.registry],
            markers=" and ".join([str(required_python_marker), *markers[package.name]]),
        )

    return PipfileLock(
        meta=LockMeta(
            hash=LockHash(sha256=pipfile_hash),
            requires=LockMetaRequires(python_version=Specifier(uv_lock.requires_python).version),
            sources=[
                LockMetaSource(
                    name=name,
                    url=url,
                )
                for url, name in source_url_name_map.items()
            ],
        ),
        default=default_packages,
        develop={},
    )
