"""Core project models."""

import os
from collections.abc import Callable
from dataclasses import field, replace
from typing import Optional

from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from mcp_guide.core.validation import validate_directory_path
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.models.constants import _NAME_REGEX, DEFAULT_ALLOWED_WRITE_PATHS


@pydantic_dataclass(frozen=True)
class Category:
    """Category configuration.

    Attributes:
        dir: Relative directory path for category content (must end with /)
        patterns: List of glob patterns (may be empty)
        name: Category name (managed by Project, must match dict key)
        description: Optional description of the category

    Note:
        Instances are immutable (frozen=True).
        Extra fields from config files are ignored.
        The name field is managed by Project.with_category() and must match
        the dictionary key in Project.categories. Use with_category() to ensure
        consistency when adding or updating categories.
        The dir field is automatically normalized to end with / if missing.
    """

    model_config = ConfigDict(extra="ignore")

    dir: str
    patterns: list[str]
    name: str = ""
    description: Optional[str] = None

    def __post_init__(self) -> None:
        """Normalize dir to ensure it ends with /."""
        if not self.dir.endswith("/"):
            object.__setattr__(self, "dir", self.dir + "/")


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
        name: Project display name (alphanumeric, hyphens, underscores, 1-50 chars)
        hash: SHA256 hash of project path for unique identification
        categories: Dictionary of category configurations (name -> Category)
        collections: Dictionary of collection configurations (name -> Collection)
        allowed_paths: List of allowed filesystem paths (must end with '/')
        openspec_validated: Whether OpenSpec validation has been completed for this project
        openspec_version: OpenSpec CLI version string (e.g., "1.2.3") if detected

    Note:
        Instances are immutable (frozen=True).
        Use with_* and without_* methods to create modified copies.
        Extra fields from config files are ignored.
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    key: Optional[str] = None  # Project key from config (for disambiguation)
    hash: Optional[str] = None
    categories: dict[str, Category] = field(default_factory=dict)
    collections: dict[str, Collection] = field(default_factory=dict)
    project_flags: dict[str, FeatureValue] = field(default_factory=dict)
    allowed_write_paths: list[str] = field(default_factory=lambda: DEFAULT_ALLOWED_WRITE_PATHS.copy())
    additional_read_paths: list[str] = field(default_factory=list)
    openspec_validated: bool = False
    openspec_version: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 50:
            raise ValueError("Project name must be between 1 and 50 characters")
        if not _NAME_REGEX.match(v):
            raise ValueError("Project name must contain only alphanumeric characters, underscores, and hyphens")
        return v

    @field_validator("allowed_write_paths")
    @classmethod
    def validate_allowed_write_paths(cls, v: list[str]) -> list[str]:
        """Validate that all allowed write paths are safe, consistent, and relative."""
        for path in v:
            if not path:
                raise ValueError("Allowed write path cannot be empty")

            # Check that path is relative
            if os.path.isabs(path):
                raise ValueError(f"Write allowed path must be relative: {path}")

            # Use existing validation for security checks
            validate_directory_path(path)

            if not path.endswith("/"):
                raise ValueError(f"Allowed write path '{path}' must end with trailing slash. Use '{path}/' instead.")
        return v

    @field_validator("additional_read_paths")
    @classmethod
    def validate_additional_read_paths(cls, v: list[str]) -> list[str]:
        """Validate additional read paths are absolute and not system directories."""
        from mcp_guide.filesystem.system_directories import is_system_directory

        validated = []
        for path in v:
            if not path:
                raise ValueError("Additional read path cannot be empty")

            if not os.path.isabs(path):
                raise ValueError(f"Additional read path must be absolute: {path}")

            if is_system_directory(path):
                raise ValueError(f"System directory not allowed: {path}")

            validated.append(path)
        return validated

    @field_validator("project_flags")
    @classmethod
    def validate_project_flags(cls, v: dict[str, FeatureValue]) -> dict[str, FeatureValue]:
        from mcp_guide.feature_flags.validators import validate_flag_name, validate_flag_value

        for flag_name, flag_value in v.items():
            if not validate_flag_name(flag_name):
                raise ValueError(f"Invalid feature flag name: {flag_name}")
            if not validate_flag_value(flag_value):
                raise ValueError(f"Invalid feature flag value type for '{flag_name}': {type(flag_value)}")
        return v

    def with_category(self, name: str, category: Category) -> "Project":
        """Return new Project with category added.

        Args:
            name: Category name (used as dict key)
            category: Category object to add

        Returns:
            New Project with category added

        Note:
            If category.name differs from name parameter, category.name is
            updated to match. This ensures consistency between dict key and
            embedded name field.
        """
        # Enforce name consistency: always use the dict key as the name
        if category.name != name:
            category = replace(category, name=name)
        new_categories = {**self.categories, name: category}
        return replace(self, categories=new_categories)

    def without_category(self, name: str) -> "Project":
        """Return new Project with category removed."""
        new_categories = {k: v for k, v in self.categories.items() if k != name}
        return replace(self, categories=new_categories)

    def with_collection(self, name: str, collection: Collection) -> "Project":
        """Return new Project with collection added."""
        new_collections = {**self.collections, name: collection}
        return replace(self, collections=new_collections)

    def without_collection(self, name: str) -> "Project":
        """Return new Project with collection removed."""
        new_collections = {k: v for k, v in self.collections.items() if k != name}
        return replace(self, collections=new_collections)

    def update_category(self, name: str, updater: Callable[[Category], Category]) -> "Project":
        """Return new Project with category updated."""
        if name not in self.categories:
            raise KeyError(f"Category '{name}' not found")
        updated_category = updater(self.categories[name])
        new_categories = {**self.categories, name: updated_category}
        return replace(self, categories=new_categories)

    def update_collection(self, name: str, updater: Callable[[Collection], Collection]) -> "Project":
        """Return new Project with collection updated."""
        if name not in self.collections:
            raise KeyError(f"Collection '{name}' not found")
        updated_collection = updater(self.collections[name])
        new_collections = {**self.collections, name: updated_collection}
        return replace(self, collections=new_collections)
