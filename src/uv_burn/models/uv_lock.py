# ruff: noqa: D101

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, computed_field
from pydantic_core import Url


class DistributionArtifact(BaseModel):
    """
    Represents a single distribution artifact (sdist or wheel).

    Example TOML fragment:
      sdist = { url = "...", hash = "sha256:...", size = 1234, upload-time = "2025-01-01T00:00:00Z" }
      wheels = [
        { url = "...", hash = "...", size = 4567, upload-time = "2025-01-01T00:00:01Z" },
      ]
    """

    url: str
    hash: str
    size: int
    upload_time: datetime = Field(alias="upload-time")


class Dependency(BaseModel):
    """
    A dependency specification (both runtime and dev). Examples:

      { name = "click" }
      { name = "colorama", marker = "sys_platform == 'win32'" }
      { name = "beanie", specifier = "~=1.30.0" }
      { name = "nga-controls-library-tools-cli", editable = "packages/cli" }

    Allow extra fields for forward compatibility.
    """

    name: str
    marker: str | None = None
    specifier: str | None = None
    editable: str | None = None


class RegistrySource(BaseModel):
    registry: Url


class EditableSource(BaseModel):
    editable: str


class PackageMetadata(BaseModel):
    """
    Represents [package.metadata] section and its nested:
      requires-dist = [...]
      [package.metadata.requires-dev]
         groupname = [ ... ]

    We model 'requires-dev' subtree as a mapping of group -> list[Dependency].
    """

    requires_dist: list[Dependency] | None = Field(default=None, alias="requires-dist")
    requires_dev: dict[str, list[Dependency]] | None = Field(default=None, alias="requires-dev")


class ExternalPackage(BaseModel):
    """
    A single [[package]] entry.
    """

    name: str
    version: str
    source: RegistrySource
    dependencies: list[Dependency] = []
    sdist: DistributionArtifact | None = None
    wheels: list[DistributionArtifact] = []

    @computed_field
    @property
    def hashes(self) -> list[str]:
        """
        Returns a list of all hashes for the package's artifacts (sdist and wheels).
        """
        hashes = [whel.hash for whel in self.wheels if whel.hash]
        if self.sdist:
            hashes.append(self.sdist.hash)
        return hashes


class InternalPackage(BaseModel):
    name: str
    version: str
    source: EditableSource
    dependencies: list[Dependency] = []

    metadata: PackageMetadata


type Package = ExternalPackage | InternalPackage


class Manifest(BaseModel):
    members: list[str]


class UvLock(BaseModel):
    version: int
    revision: int
    requires_python: str = Field(alias="requires-python")
    manifest: Manifest
    packages: list[Package] = Field(alias="package")

    def packages_by_type[T: Package](self, type_: type[T]) -> list[T]:
        """
        Returns a list of packages of the specified type (ExternalPackage or InternalPackage).
        Args:
            type_ (type[T]): The type of packages to filter by.
        Returns:
            list[T]: A list of packages of the specified type.
        """
        return [pkg for pkg in self.packages if isinstance(pkg, type_)]
