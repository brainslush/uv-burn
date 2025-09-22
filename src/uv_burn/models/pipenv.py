from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import Url


class PipfileSource(BaseModel):
    """
    Represents a source in a Pipfile.
    """

    name: str
    url: Url
    verify_ssl: Annotated[bool, Field(alias="verify_ssl")]

    model_config = ConfigDict(validate_by_name=True)


class PipfileRequires(BaseModel):
    """
    Represents the 'requires' section in a Pipfile.
    """

    python_version: str

    model_config = ConfigDict(validate_by_name=True, serialize_by_alias=True)


class PackageDefinition(BaseModel):
    """
    Represents a package with its version and optional extras.
    """

    version: str
    extras: list[str] | None = None
    markers: str | None = None
    index: str | None = None

    model_config = ConfigDict(validate_by_name=True)


class PackageLocal(BaseModel):
    """
    Represents a local package.
    """

    path: str
    editable: bool = True
    markers: str | None = None

    model_config = ConfigDict(validate_by_name=True)


class PackageGit(BaseModel):
    """
    Represents a package from a git repository.
    """

    url: str
    ref: str | None = None
    markers: str | None = None

    model_config = ConfigDict(validate_by_name=True)


type PipfilePackage = PackageDefinition | PackageLocal | PackageGit


class Pipfile(BaseModel):
    """
    Represents a Pipfile.

    - 'source' is a list of [[source]] tables.
    - 'packages' and 'dev-packages' are simple name -> version-spec mappings (strings).
    - 'requires' typical keys: python_version
    """

    sources: Annotated[list[PipfileSource], Field(alias="source")] = []
    packages: Annotated[dict[str, str | PipfilePackage], Field(alias="packages")] = {}
    dev_packages: Annotated[dict[str, str | PipfilePackage], Field(alias="dev-packages")] = {}
    requires: PipfileRequires

    model_config = ConfigDict(validate_by_name=True, serialize_by_alias=True)


class MetaHash(BaseModel):
    """
    Represents the metadata for a hash calculation.
    """

    sources: list[PipfileSource] = []
    requires: PipfileRequires


class PipfileHash(BaseModel):
    """
    Represents a model on whichs basis the hash is calculated.
    """

    meta: Annotated[MetaHash, Field(alias="_meta")]
    default: dict[str, str | PipfilePackage] = {}
    develop: dict[str, str | PipfilePackage] = {}

    model_config = ConfigDict(validate_by_name=True, serialize_by_alias=True)
