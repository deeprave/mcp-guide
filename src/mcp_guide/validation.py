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
        category_names: Category names or expressions to validate

    Raises:
        ArgValidationError: If any categories don't exist (lists all missing)
    """
    from mcp_guide.models import ExpressionParseError
    from mcp_guide.utils.content_common import parse_expression

    errors = []
    for entry in category_names:
        try:
            expressions = parse_expression(entry)
            for expr in expressions:
                if expr.name not in project.categories:
                    errors.append({"field": "categories", "message": f"Category '{expr.name}' does not exist"})
        except ExpressionParseError:
            # If parsing fails, treat as literal category name
            if entry not in project.categories:
                errors.append({"field": "categories", "message": f"Category '{entry}' does not exist"})

    if errors:
        raise ArgValidationError(errors)
