"""Immutable data models for project configuration."""

import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, NamedTuple, Optional

from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from mcp_core.mcp_log import get_logger
from mcp_core.validation import validate_directory_path

logger = get_logger(__name__)

if TYPE_CHECKING:
    from mcp_guide.session import Session

from mcp_guide.feature_flags.types import FeatureValue

# Default allowed filesystem paths for projects.
# These paths are relative to the project root and must have trailing slashes.
# Used by the filesystem interaction feature for security fencing.
# See: openspec/changes/agent-server-filesystem-interaction/specs/filesystem-interaction/spec.md
DEFAULT_ALLOWED_WRITE_PATHS: list[str] = [
    "openspec/",
    "memory/",
    "specs/",
    "templates/",
    "tasks/",
    "docs/",
    ".todo/",
    ".issues/",
]

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


def _format_categories_and_collections(project: "Project", verbose: bool) -> tuple[Any, Any]:
    """Format categories and collections for tool responses.

    Args:
        project: Project to format
        verbose: If True, include full details; if False, names only

    Returns:
        Tuple of (collections, categories) formatted data
    """
    from typing import Union

    collections: Union[list[dict[str, Any]], list[str]]
    categories: Union[list[dict[str, Any]], list[str]]

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

    return collections, categories


async def format_project_data(
    project: "Project", verbose: bool = False, session: Optional["Session"] = None
) -> dict[str, Any]:
    """Format project data for tool responses.

    Args:
        project: Project to format
        verbose: If True, include full details; if False, names only
        session: Session for flag resolution (optional)

    Returns:
        Formatted project data dictionary
    """
    collections, categories = _format_categories_and_collections(project, verbose)
    result: dict[str, Any] = {"collections": collections, "categories": categories}

    # Add resolved flags if session is available
    if session is not None:
        flags = await resolve_all_flags(session)
        result["flags"] = flags if verbose else list(flags.keys())
    return result


async def resolve_all_flags(session: "Session") -> dict[str, Any]:
    """Resolve all flags by merging project and global flags.

    Returns:
        Resolved flags dictionary, or empty dict if resolution fails
    """
    from mcp_guide.feature_flags.resolution import resolve_flag

    try:
        # Get all flags
        project_flags = await session.project_flags().list()
        global_flags = await session.feature_flags().list()

        # Get all unique flag names
        all_flag_names = set(project_flags.keys()) | set(global_flags.keys())

        # Resolve each flag
        resolved = {}
        for name in all_flag_names:
            value = resolve_flag(name, project_flags, global_flags)
            if value is not None:
                resolved[name] = value

        return resolved
    except Exception as e:
        # Log unexpected errors for debugging, but continue with empty flags
        # since flags are supplementary data
        logger.debug(f"Flag resolution failed: {e}")
        return {}


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
        name: Project display name (alphanumeric, hyphens, underscores, 1-50 chars)
        hash: SHA256 hash of project path for unique identification
        categories: Dictionary of category configurations (name -> Category)
        collections: Dictionary of collection configurations (name -> Collection)
        allowed_paths: List of allowed filesystem paths (must end with '/')

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
        """Return new Project with category added."""
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
        from mcp_guide.feature_flags.validators import validate_flag_name, validate_flag_value

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
