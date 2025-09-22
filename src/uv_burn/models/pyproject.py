from typing import Annotated

from pydantic import BaseModel, Field
from pydantic_core import Url


class Project(BaseModel):
    """
    A model for the `project` section of pyproject.toml files.
    """

    name: str
    version: str
    description: str | None = None
    requires_python: Annotated[str, Field(alias="requires-python")]
    dependencies: list[str] = []
    classifiers: list[str] = []
    readme: str | None = None


class DependencyGroups(BaseModel):
    """
    A model for the `dependency-groups` section of pyproject.toml files.
    Is currently only used to parse the `dev` group as Veracode does not scan dev dependencies.
    """

    dev: list[str] = []


class UvSourceSpec(BaseModel):
    """
    A model for a source specification in the `tool.uv` section of pyproject.toml files.
    """

    workspace: bool | None = None
    path: str | None = None
    git: str | None = None
    rev: str | None = None
    index: str | None = None


class Index(BaseModel):
    """
    A model for an index entry in the `tool.uv` section of pyproject.toml files.
    """

    name: str
    url: Url


class UvTool(BaseModel):
    """
    A model for the `tool.uv` section of pyproject.toml files.
    """

    sources: dict[str, UvSourceSpec] = {}
    indices: Annotated[list[Index], Field(alias="index")] = []


class Tool(BaseModel):
    """
    A model for the `tool` section of pyproject.toml files.
    """

    uv: UvTool | None = None


class PyProject(BaseModel):
    """
    A model for pyproject.toml files with explicit fields for the `tool.uv` section.
    """

    project: Project
    dependency_groups: DependencyGroups | None = Field(default=None, alias="dependency-groups")
    tool: Tool | None = None
