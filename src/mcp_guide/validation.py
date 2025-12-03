"""Validation functions for mcp_guide."""

from mcp_core.validation import ArgValidationError
from mcp_guide.models import Project


def validate_category_exists(project: Project, category_name: str) -> None:
    """Validate a single category reference exists.

    Args:
        project: Project instance
        category_name: Category name to validate

    Raises:
        ArgValidationError: If category doesn't exist
    """
    category_names = {cat.name for cat in project.categories}
    if category_name not in category_names:
        raise ArgValidationError([{"field": "category", "message": f"Category '{category_name}' does not exist"}])


def validate_categories_exist(project: Project, category_names: list[str]) -> None:
    """Validate multiple category references exist.

    Args:
        project: Project instance
        category_names: Category names to validate

    Raises:
        ArgValidationError: If any categories don't exist (lists all missing)
    """
    existing_names = {cat.name for cat in project.categories}
    if errors := [
        {"field": "categories", "message": f"Category '{name}' does not exist"}
        for name in category_names
        if name not in existing_names
    ]:
        raise ArgValidationError(errors)
