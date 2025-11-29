"""Immutable data models for project configuration."""

import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Optional

from pydantic import field_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

# Name validation pattern: alphanumeric, underscore, hyphen
NAME_PATTERN = r"^[a-zA-Z0-9_-]+$"
_NAME_REGEX = re.compile(NAME_PATTERN)


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
    """

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
    """

    name: str
    categories: list[str]
    description: str = ""

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
    """

    name: str
    categories: list[Category] = field(default_factory=list)
    collections: list[Collection] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 50:
            raise ValueError("Project name must be between 1 and 50 characters")
        if not _NAME_REGEX.match(v):
            raise ValueError("Project name must contain only alphanumeric characters, underscores, and hyphens")
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


@dataclass
class SessionState:
    """Mutable runtime state for a session."""

    current_dir: str = ""
    cache: dict[str, object] = field(default_factory=dict)
