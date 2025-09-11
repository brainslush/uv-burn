from typing import Annotated, Literal

from packaging.utils import InvalidSdistFilename, InvalidWheelFilename, parse_sdist_filename, parse_wheel_filename
from pydantic import BaseModel, ConfigDict, Field, computed_field


class Hashes(BaseModel):
    """
    Represents the hashes of a file.
    """

    sha256: str


class MetadataSha(BaseModel):
    """
    Represents the metadata SHA256 hash of a file.
    """

    sha256: str


class FileEntry(BaseModel):
    """
    Represents a file entry in the PyPI simple API response.
    """

    filename: str
    hashes: Hashes
    requires_python: Annotated[str | None, Field(default=None, alias="requires-python")]
    size: int
    upload_time: Annotated[str, Field(alias="upload-time")]
    url: str
    yanked: bool | str


class WhlFileEntry(FileEntry):
    """
    Represents a wheel file entry in the PyPI simple API response.
    """

    core_metadata: Annotated[MetadataSha, Field(alias="core-metadata")]
    data_dist_info_metadata: Annotated[MetadataSha, Field(alias="data-dist-info-metadata")]

    @computed_field
    @property
    def version(self) -> str | None:
        """
        Extracts and returns the version from the wheel filename.
        """
        try:
            _, version, _, _ = parse_wheel_filename(self.filename)
        except InvalidWheelFilename:
            return None
        return str(version)


class DistFileEntry(FileEntry):
    """
    Represents a distribution file entry in the PyPI simple API response.
    """

    core_metadata: Annotated[Literal[False], Field(alias="core-metadata")]
    data_dist_info_metadata: Annotated[Literal[False], Field(alias="data-dist-info-metadata")]

    @computed_field
    @property
    def version(self) -> str | None:
        """
        Extracts and returns the version from the distribution filename.
        """
        try:
            _, version = parse_sdist_filename(self.filename)
        except InvalidSdistFilename:
            return None
        return str(version)


class Meta(BaseModel):
    """
    Represents the metadata of the PyPI simple API response.
    """

    last_serial: Annotated[int, Field(alias="_last-serial")]
    api_version: Annotated[str, Field(alias="api-version")]


class ProjectStatus(BaseModel):
    """
    Represents the project status in the PyPI simple API response.
    """

    status: str


class PyPiSimpleResponse(BaseModel):
    """
    Represents the response from the PyPI simple API.
    """

    files: list[WhlFileEntry | DistFileEntry]
    meta: Meta
    name: str
    project_status: Annotated[ProjectStatus, Field(alias="project-status")]
    versions: list[str]

    model_config = ConfigDict(populate_by_name=True)
