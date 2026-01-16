"""Validation functions for mcp_guide."""

from mcp_guide.core.validation import ArgValidationError
from mcp_guide.models import Project


class InvalidProjectNameError(ValueError):
    """Raised when project name validation fails."""

    pass


def validate_category_exists(project: Project, category_name: str) -> None:
    """Validate a single category reference exists.

    Args:
        project: Project instance
        category_name: Category name to validate

    Raises:
        ArgValidationError: If category doesn't exist
    """
    # Use dict lookup for O(1) existence check
    if category_name not in project.categories:
        raise ArgValidationError([{"field": "category", "message": f"Category '{category_name}' does not exist"}])


def validate_categories_exist(project: Project, category_names: list[str]) -> None:
    """Validate multiple category references exist.

    Args:
        project: Project instance
        category_names: Category names to validate

    Raises:
        ArgValidationError: If any categories don't exist (lists all missing)
    """
    # Use dict keys for O(1) existence checks
    if errors := [
        {"field": "categories", "message": f"Category '{name}' does not exist"}
        for name in category_names
        if name not in project.categories
    ]:
        raise ArgValidationError(errors)
