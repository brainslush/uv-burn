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
      { name = "sub-package", editable = "packages/cli" }

    Allow extra fields for forward compatibility.
    """

    name: str
    marker: str | None = None
    specifier: str | None = None
    editable: str | None = None


class RegistrySource(BaseModel):
    """
    Represents a registry source for a package.
    Example TOML fragment:
      source = { registry = "https://pypi.org/simple" }
    """

    registry: Url


class EditableSource(BaseModel):
    """
    Represents an editable source for a package.
    Should actually not be existent in the lockfile, as editable packages can not be accessed by Veracode.
    """

    editable: str


class VirtualSource(BaseModel):
    """
    Represents a virtual source for a package.
    Example TOML fragment:
      source = { virtual = "." }
    """

    virtual: str


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
    """
    A single [[package]] entry for an internal (editable) package.
    """

    name: str
    version: str
    source: EditableSource | VirtualSource
    dependencies: list[Dependency] = []

    metadata: PackageMetadata


type Package = ExternalPackage | InternalPackage


class UvLock(BaseModel):
    """
    The root model for the uv.lock file.
    """

    version: int
    revision: int
    requires_python: str = Field(alias="requires-python")
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
