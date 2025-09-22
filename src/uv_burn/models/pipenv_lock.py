from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import Url


class LockHash(BaseModel):
    """
    Represents the 'hash' section of pipenv.lock.
    """

    sha256: str

    model_config = ConfigDict(validate_by_name=True)


class LockMetaRequires(BaseModel):
    """
    Represents the 'requires' section of pipenv.lock.
    """

    python_version: str | None = None

    model_config = ConfigDict(validate_by_name=True)


class LockMetaSource(BaseModel):
    """
    Represents a source entry in the 'sources' section of pipenv.lock.
    """

    name: str
    url: Url
    verify_ssl: bool = True

    model_config = ConfigDict(validate_by_name=True)


class LockMeta(BaseModel):
    """
    Represents the '_meta' section of pipenv.lock.
    """

    hash_: LockHash = Field(alias="hash")
    pipfile_spec: int = Field(default=6, alias="pipfile-spec")
    requires: LockMetaRequires
    sources: list[LockMetaSource]

    model_config = ConfigDict(validate_by_name=True, serialize_by_alias=True)


class LockPackageEntry(BaseModel):
    """
    Represents an entry under 'default' or 'develop' in pipenv.lock.

    Common keys:
      version: str (e.g. "==1.2.3")
      hashes: list[str]
      index: "pypi"
      markers: optional environment markers string
    Extra fields (e.g. extras, editable, file, ref) are allowed.
    """

    version: str
    hashes: list[str]
    index: str
    markers: str

    model_config = ConfigDict(validate_by_name=True)


class PipfileLock(BaseModel):
    """
    Represents the entire pipenv.lock file.
    """

    meta: Annotated[LockMeta, Field(serialization_alias="_meta")]
    default: dict[str, LockPackageEntry]
    develop: dict[str, LockPackageEntry] = {}

    model_config = ConfigDict(validate_by_name=True, serialize_by_alias=True)
