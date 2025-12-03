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
    if not any(cat.name == category_name for cat in project.categories):
        raise ArgValidationError([{"field": "category", "message": f"Category '{category_name}' does not exist"}])


def validate_categories_exist(project: Project, category_names: list[str]) -> None:
    """Validate multiple category references exist.

    Args:
        project: Project instance
        category_names: Category names to validate

    Raises:
        ArgValidationError: If any categories don't exist (lists all missing)
    """
    errors = []
    for name in category_names:
        if not any(cat.name == name for cat in project.categories):
            errors.append({"field": "categories", "message": f"Category '{name}' does not exist"})

    if errors:
        raise ArgValidationError(errors)
