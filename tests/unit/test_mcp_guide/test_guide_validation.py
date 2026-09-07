"""Category reference validation reports every missing expression."""

import pytest

from mcp_guide.core.validation import ArgValidationError
from mcp_guide.models import Category, Project
from mcp_guide.validation import validate_categories_exist


def test_existing_categories_and_empty_selections_are_valid():
    project = Project(
        name="test",
        categories={
            "docs": Category(dir="docs", patterns=["*.md"]),
            "api": Category(dir="api", patterns=["*.py"]),
        },
    )
    validate_categories_exist(project, ["docs", "api"])
    validate_categories_exist(project, [])
    validate_categories_exist(Project(name="empty"), [])


@pytest.mark.parametrize(
    "existing,selected,missing",
    [
        (["docs", "api"], ["docs", "missing1", "api", "missing2"], ["missing1", "missing2"]),
        (["docs", "api"], ["missing1", "missing2"], ["missing1", "missing2"]),
        ([], ["docs", "api"], ["docs", "api"]),
    ],
    ids=["partly-missing", "all-missing", "empty-project"],
)
def test_missing_categories_are_reported_together(existing, selected, missing):
    project = Project(name="test", categories={name: Category(dir=name, patterns=["*"]) for name in existing})
    with pytest.raises(ArgValidationError) as failure:
        validate_categories_exist(project, selected)
    assert failure.value.errors == [
        {"field": "categories", "message": f"Category '{name}' does not exist"} for name in missing
    ]
