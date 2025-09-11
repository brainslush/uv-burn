# ruff: noqa: D101

from typing import Annotated

from pydantic import BaseModel, Field
from pydantic_core import Url


class Project(BaseModel):
    name: str
    version: str
    description: str | None = None
    requires_python: Annotated[str, Field(alias="requires-python")]
    dependencies: list[str] = []
    classifiers: list[str] = []
    readme: str | None = None


class DependencyGroups(BaseModel):
    dev: list[str] = []


class UvSourceSpec(BaseModel):
    workspace: bool | None = None
    path: str | None = None
    git: str | None = None
    rev: str | None = None
    index: str | None = None


class Index(BaseModel):
    name: str
    url: Url


class UvTool(BaseModel):
    sources: dict[str, UvSourceSpec] = {}
    indices: Annotated[list[Index], Field(alias="index")] = []


class Tool(BaseModel):
    uv: UvTool | None = None


class PyProject(BaseModel):
    project: Project
    dependency_groups: DependencyGroups | None = Field(default=None, alias="dependency-groups")
    tool: Tool | None = None
