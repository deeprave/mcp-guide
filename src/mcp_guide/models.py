"""Immutable data models for project configuration."""

import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any, NamedTuple, Optional

from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from mcp_guide.feature_flags.types import FeatureValue

# Name validation: Unicode alphanumeric, underscore, hyphen
NAME_PATTERN = r"^[\w-]+$"
_NAME_REGEX = re.compile(NAME_PATTERN, re.UNICODE)


# Custom exceptions for better error handling
class NoProjectError(Exception):
    """Raised when no project or session is available."""

    pass


class CategoryNotFoundError(Exception):
    """Raised when a category is not found in the project."""

    def __init__(self, category_name: str):
        self.category_name = category_name
        super().__init__(f"Category '{category_name}' not found in project")


class CollectionNotFoundError(Exception):
    """Raised when a collection is not found in the project."""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        super().__init__(f"Collection '{collection_name}' not found in project")


class ExpressionParseError(Exception):
    """Raised when expression parsing fails."""

    pass


class FileReadError(Exception):
    """Raised when file reading fails."""

    pass


class DocumentExpression(NamedTuple):
    """Document expression for parsing user input before resolution.

    Used to parse category/pattern syntax with lenient validation.
    Resolution logic determines if name refers to category or collection.

    Attributes:
        raw_input: Original user input string
        name: Parsed category or collection name
        patterns: Optional list of parsed patterns
    """

    raw_input: str
    name: str
    patterns: Optional[list[str]] = None


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
            {"name": name, "description": c.description, "categories": c.categories}
            for name, c in project.collections.items()
        ]
        categories = [
            {"name": name, "dir": c.dir, "patterns": list(c.patterns), "description": c.description}
            for name, c in project.categories.items()
        ]
    else:
        collections = list(project.collections.keys())
        categories = list(project.categories.keys())

    return {"collections": collections, "categories": categories}


@pydantic_dataclass(frozen=True)
class Category:
    """Category configuration.

    Attributes:
        dir: Directory path for category content
        patterns: List of glob patterns (may be empty)
        description: Optional description of the category

    Note:
        Instances are immutable (frozen=True).
        Extra fields from config files are ignored.
        Name is stored as dict key in Project.categories.
    """

    model_config = ConfigDict(extra="ignore")

    dir: str
    patterns: list[str]
    description: Optional[str] = None


@pydantic_dataclass(frozen=True)
class Collection:
    """Collection grouping related categories.

    Attributes:
        categories: List of category names in this collection
        description: Optional description of the collection

    Note:
        Instances are immutable (frozen=True).
        Extra fields from config files are ignored.
        Name is stored as dict key in Project.collections.
    """

    model_config = ConfigDict(extra="ignore")

    categories: list[str]
    description: Optional[str] = None


@pydantic_dataclass(frozen=True)
class Project:
    """Immutable project configuration.

    Attributes:
        name: Project name (alphanumeric, hyphens, underscores, 1-50 chars)
        categories: Dictionary of category configurations (name -> Category)
        collections: Dictionary of collection configurations (name -> Collection)
        created_at: Timestamp when project was created
        updated_at: Timestamp when project was last updated

    Note:
        Instances are immutable (frozen=True).
        Use with_* and without_* methods to create modified copies.
        Extra fields from config files are ignored.
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    categories: dict[str, Category] = field(default_factory=dict)
    collections: dict[str, Collection] = field(default_factory=dict)
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

    def with_category(self, name: str, category: Category) -> "Project":
        """Return new Project with category added."""
        new_categories = {**self.categories, name: category}
        return replace(self, categories=new_categories, updated_at=datetime.now())

    def without_category(self, name: str) -> "Project":
        """Return new Project with category removed."""
        new_categories = {k: v for k, v in self.categories.items() if k != name}
        return replace(self, categories=new_categories, updated_at=datetime.now())

    def with_collection(self, name: str, collection: Collection) -> "Project":
        """Return new Project with collection added."""
        new_collections = {**self.collections, name: collection}
        return replace(self, collections=new_collections, updated_at=datetime.now())

    def without_collection(self, name: str) -> "Project":
        """Return new Project with collection removed."""
        new_collections = {k: v for k, v in self.collections.items() if k != name}
        return replace(self, collections=new_collections, updated_at=datetime.now())

    def update_category(self, name: str, updater: Callable[[Category], Category]) -> "Project":
        """Return new Project with category updated."""
        if name not in self.categories:
            raise KeyError(f"Category '{name}' not found")
        updated_category = updater(self.categories[name])
        new_categories = {**self.categories, name: updated_category}
        return replace(self, categories=new_categories, updated_at=datetime.now())

    def update_collection(self, name: str, updater: Callable[[Collection], Collection]) -> "Project":
        """Return new Project with collection updated."""
        if name not in self.collections:
            raise KeyError(f"Collection '{name}' not found")
        updated_collection = updater(self.collections[name])
        new_collections = {**self.collections, name: updated_collection}
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
