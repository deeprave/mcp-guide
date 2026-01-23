"""Immutable data models for project configuration."""

# Re-export all models from submodules
from mcp_guide.models.config import ConfigFile
from mcp_guide.models.constants import _NAME_REGEX, DEFAULT_ALLOWED_WRITE_PATHS, NAME_PATTERN
from mcp_guide.models.exceptions import (
    CategoryNotFoundError,
    CollectionNotFoundError,
    ExpressionParseError,
    FileReadError,
    NoProjectError,
)
from mcp_guide.models.expression import DocumentExpression
from mcp_guide.models.formatting import format_project_data, resolve_all_flags
from mcp_guide.models.profile_config import ProfileCategory, ProfileCollection
from mcp_guide.models.project import Category, Collection, Project
from mcp_guide.models.session import SessionState

__all__ = [
    # Constants
    "DEFAULT_ALLOWED_WRITE_PATHS",
    "NAME_PATTERN",
    "_NAME_REGEX",
    # Exceptions
    "NoProjectError",
    "CategoryNotFoundError",
    "CollectionNotFoundError",
    "ExpressionParseError",
    "FileReadError",
    # Models
    "Category",
    "Collection",
    "Project",
    "ConfigFile",
    "SessionState",
    "DocumentExpression",
    "ProfileCategory",
    "ProfileCollection",
    # Utilities
    "format_project_data",
    "resolve_all_flags",
]
