"""Immutable data models for project configuration."""

import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, Optional

from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from mcp_guide.feature_flags.types import FeatureValue

# Name validation: Unicode alphanumeric, underscore, hyphen
NAME_PATTERN = r"^[\w-]+$"
_NAME_REGEX = re.compile(NAME_PATTERN, re.UNICODE)


def format_project_data(project: "Project", verbose: bool = False) -> dict[str, Any]:
    """Format project data for tool responses.

    Args:
        project: Project to format
        verbose: If True, include full details; if False, names only

    Returns:
        Formatted project data dictionary
    """
    collections: list[dict[str, str | list[str] | None]] | list[str]
    categories: list[dict[str, str | list[str] | None]] | list[str]

    if verbose:
        collections = [
            {"name": c.name, "description": c.description, "categories": c.categories} for c in project.collections
        ]
        categories = [
            {"name": c.name, "dir": c.dir, "patterns": list(c.patterns), "description": c.description}
            for c in project.categories
        ]
    else:
        collections = [c.name for c in project.collections]
        categories = [c.name for c in project.categories]

    return {"collections": collections, "categories": categories}


@pydantic_dataclass(frozen=True)
class Category:
    """Category configuration.

    Attributes:
        name: Category name (alphanumeric, hyphens, underscores, 1-30 chars)
        dir: Directory path for category content
        patterns: List of glob patterns (may be empty)
        description: Optional description of the category

    Note:
        Instances are immutable (frozen=True).
        Extra fields from config files are ignored.
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    dir: str
    patterns: list[str]
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 30:
            raise ValueError("Category name must be between 1 and 30 characters")
        if not _NAME_REGEX.match(v):
            raise ValueError("Category name must contain only alphanumeric characters, underscores, and hyphens")
        return v


@pydantic_dataclass(frozen=True)
class Collection:
    """Collection grouping related categories.

    Attributes:
        name: Collection name (alphanumeric, hyphens, underscores, 1-30 chars)
        categories: List of category names in this collection
        description: Optional description of the collection

    Note:
        Instances are immutable (frozen=True).
        Extra fields from config files are ignored.
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    categories: list[str]
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 30:
            raise ValueError("Collection name must be between 1 and 30 characters")
        if not _NAME_REGEX.match(v):
            raise ValueError("Collection name must contain only alphanumeric characters, underscores, and hyphens")
        return v


@pydantic_dataclass(frozen=True)
class Project:
    """Immutable project configuration.

    Attributes:
        name: Project name (alphanumeric, hyphens, underscores, 1-50 chars)
        categories: List of category configurations
        collections: List of collection configurations
        created_at: Timestamp when project was created
        updated_at: Timestamp when project was last updated

    Note:
        Instances are immutable (frozen=True).
        Use with_* and without_* methods to create modified copies.
        Extra fields from config files are ignored.
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    categories: list[Category] = field(default_factory=list)
    collections: list[Collection] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    project_flags: dict[str, FeatureValue] = field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 50:
            raise ValueError("Project name must be between 1 and 50 characters")
        if not _NAME_REGEX.match(v):
            raise ValueError("Project name must contain only alphanumeric characters, underscores, and hyphens")
        return v

    @field_validator("project_flags")
    @classmethod
    def validate_project_flags(cls, v: dict[str, FeatureValue]) -> dict[str, FeatureValue]:
        from mcp_guide.feature_flags.validation import validate_flag_name, validate_flag_value
        
        for flag_name, flag_value in v.items():
            if not validate_flag_name(flag_name):
                raise ValueError(f"Invalid feature flag name: {flag_name}")
            if not validate_flag_value(flag_value):
                raise ValueError(f"Invalid feature flag value type for '{flag_name}': {type(flag_value)}")
        return v

    def with_category(self, category: Category) -> "Project":
        """Return new Project with category added."""
        return replace(self, categories=[*self.categories, category], updated_at=datetime.now())

    def without_category(self, name: str) -> "Project":
        """Return new Project with category removed."""
        new_categories = [c for c in self.categories if c.name != name]
        return replace(self, categories=new_categories, updated_at=datetime.now())

    def with_collection(self, collection: Collection) -> "Project":
        """Return new Project with collection added."""
        return replace(self, collections=[*self.collections, collection], updated_at=datetime.now())

    def without_collection(self, name: str) -> "Project":
        """Return new Project with collection removed."""
        new_collections = [c for c in self.collections if c.name != name]
        return replace(self, collections=new_collections, updated_at=datetime.now())

    def update_category(self, name: str, updater: Callable[[Category], Category]) -> "Project":
        """Return new Project with category updated."""
        new_categories = [updater(c) if c.name == name else c for c in self.categories]
        return replace(self, categories=new_categories, updated_at=datetime.now())

    def update_collection(self, name: str, updater: Callable[[Collection], Collection]) -> "Project":
        """Return new Project with collection updated."""
        new_collections = [updater(c) if c.name == name else c for c in self.collections]
        return replace(self, collections=new_collections, updated_at=datetime.now())


@pydantic_dataclass(frozen=True)
class GlobalConfig:
    """Global configuration with feature flags.

    Attributes:
        feature_flags: Dictionary of global feature flags with FeatureValue types
        docroot: Document root directory path

    Note:
        Instances are immutable (frozen=True).
        Extra fields from config files are ignored.
        Feature flag names and values are validated.
    """

    model_config = ConfigDict(extra="ignore")

    feature_flags: dict[str, FeatureValue] = field(default_factory=dict)
    docroot: str = ""

    @field_validator("feature_flags")
    @classmethod
    def validate_feature_flags(cls, v: dict[str, FeatureValue]) -> dict[str, FeatureValue]:
        from mcp_guide.feature_flags.validation import validate_flag_name, validate_flag_value
        
        for flag_name, flag_value in v.items():
            if not validate_flag_name(flag_name):
                raise ValueError(f"Invalid feature flag name: {flag_name}")
            if not validate_flag_value(flag_value):
                raise ValueError(f"Invalid feature flag value type for '{flag_name}': {type(flag_value)}")
        return v


@dataclass
class SessionState:
    """Mutable runtime state for a session."""

    current_dir: str = ""
    cache: dict[str, object] = field(default_factory=dict)
