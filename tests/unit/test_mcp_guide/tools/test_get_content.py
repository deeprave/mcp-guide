"""Tests for get_content unified access tool."""

import pytest
from pydantic import ValidationError
from tests.helpers import request_context_for, tool_result_payload

from mcp_guide.models import Category, Collection, Project
from mcp_guide.tools.tool_content import ContentArgs, get_content


async def invoke_get_content(args: ContentArgs, session) -> dict:
    """Call the application get_content handler with an explicit RequestContext."""
    return tool_result_payload(await get_content.__wrapped__(args, await request_context_for(session)))


def create_mock_session(tmp_path, project_data, project_flags_data=None, feature_flags_data=None):
    """Create a mock session with required methods."""

    project_flags_data = project_flags_data or {}
    feature_flags_data = feature_flags_data or {}
    from mcp_guide.runtime import GuideRuntime, create_runtime
    from mcp_guide.session import Session

    runtime: GuideRuntime
    config_dir = tmp_path / "cfg"
    config_dir.mkdir(exist_ok=True)
    runtime = create_runtime(lambda _owner: Session(runtime), config_dir=str(config_dir), docroot=tmp_path)

    class MockSession:
        session_id = None

        class TaskManager:
            async def process_result(self, result):
                return result

        task_manager = TaskManager()

        async def get_project(self):
            return project_data

        @property
        def project_is_bound(self):
            return project_data is not None

        @property
        def project(self):
            return project_data

        @property
        def runtime(self):
            return runtime

        async def get_docroot(self):
            return str(tmp_path)

        def resolve_document_path(self, relative_path):
            from pathlib import Path

            return Path(tmp_path) / relative_path

        def project_flags(self):
            class MockProjectFlags:
                async def list(self):
                    return project_flags_data

            return MockProjectFlags()

        def feature_flags(self):
            class MockFeatureFlags:
                async def list(self):
                    return feature_flags_data

            return MockFeatureFlags()

    return MockSession()


def test_content_args_exists():
    """Test that ContentArgs class exists."""
    assert ContentArgs is not None


def test_expression_field_is_required():
    """Test that expression field is required."""
    with pytest.raises(ValidationError):
        ContentArgs()


def test_pattern_field_is_optional():
    """Test that pattern field is optional."""
    args = ContentArgs(expression="test")
    assert args.pattern is None


def test_schema_validates_correctly():
    """Test that schema validates correctly."""
    args = ContentArgs(expression="test", pattern="*.md")
    assert args.expression == "test"
    assert args.pattern == "*.md"


@pytest.mark.anyio
async def test_get_content_collection_only(tmp_path):
    """Test get_content with collection-only match."""
    category_dir = tmp_path / "guide"
    category_dir.mkdir()
    (category_dir / "README").write_text("# Test")

    project_data = Project(
        name="test",
        categories={"guide": Category(dir="guide", name="guide", patterns=["README", "guide"])},
        collections={"all": Collection(categories=["guide"])},
    )

    result = await invoke_get_content(ContentArgs(expression="all"), create_mock_session(tmp_path, project_data))
    assert result["success"] is True


@pytest.mark.anyio
async def test_get_content_category_only(tmp_path):
    """Test get_content with category-only match."""
    category_dir = tmp_path / "guide"
    category_dir.mkdir()
    (category_dir / "README").write_text("# Test")

    project_data = Project(
        name="test",
        categories={"guide": Category(dir="guide", name="guide", patterns=["README", "guide"])},
        collections={},
    )

    result = await invoke_get_content(ContentArgs(expression="guide"), create_mock_session(tmp_path, project_data))
    assert result["success"] is True


@pytest.mark.anyio
async def test_get_content_deduplicates(tmp_path):
    """Test get_content with collection and category names that overlap."""
    category_dir = tmp_path / "guide"
    category_dir.mkdir()
    (category_dir / "README").write_text("# Test")

    project_data = Project(
        name="test",
        categories={"guide": Category(dir="guide", name="guide", patterns=["README", "guide"])},
        collections={"guide": Collection(categories=["guide"])},
    )

    result = await invoke_get_content(ContentArgs(expression="guide"), create_mock_session(tmp_path, project_data))
    assert result["success"] is True
    assert "# Test" in result["value"]


@pytest.mark.anyio
async def test_get_content_empty_result(tmp_path):
    """Test get_content with no matching files."""
    category_dir = tmp_path / "empty"
    category_dir.mkdir()

    project_data = Project(
        name="test",
        categories={"empty": Category(dir="empty", name="empty", patterns=["README", "guide"])},
        collections={},
    )

    result = await invoke_get_content(ContentArgs(expression="empty"), create_mock_session(tmp_path, project_data))
    assert result["success"] is True
    assert "No matching content found" in result["value"]
    assert "instruction" in result


@pytest.mark.anyio
async def test_get_content_pattern_override(tmp_path):
    """Test get_content with pattern override."""
    category_dir = tmp_path / "docs"
    category_dir.mkdir()
    (category_dir / "README").write_text("# Test")
    (category_dir / "guide").write_text("Guide content")
    (category_dir / "tutorial").write_text("Tutorial content")

    project_data = Project(
        name="test",
        categories={"docs": Category(dir="docs", name="docs", patterns=["README", "guide", "tutorial"])},
        collections={},
    )

    result = await invoke_get_content(
        ContentArgs(expression="docs", pattern="README"), create_mock_session(tmp_path, project_data)
    )
    assert result["success"] is True
    assert "# Test" in result["value"]
    assert "Guide content" not in result["value"]
    assert "Tutorial content" not in result["value"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "scenario,expression,has_collection",
    [
        ("category_only", "docs", False),
        ("collection", "all", True),
    ],
    ids=["category_only", "collection"],
)
async def test_get_content_metadata_scenarios(tmp_path, scenario, expression, has_collection):
    """Test that category and collection searches set appropriate metadata on FileInfo."""
    category_dir = tmp_path / "docs"
    category_dir.mkdir()
    (category_dir / "README").write_text("# Test")

    collections = {"all": Collection(categories=["docs"])} if has_collection else {}
    project_data = Project(
        name="test",
        categories={"docs": Category(dir="docs", name="docs", patterns=["README", "guide"])},
        collections=collections,
    )

    result = await invoke_get_content(ContentArgs(expression=expression), create_mock_session(tmp_path, project_data))
    assert result["success"] is True
    assert "# Test" in result["value"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "project_flags,feature_flags,expected_format",
    [
        ({}, {}, "none"),
        ({"content-format": "plain"}, {}, "plain"),
        ({"content-format": "mime"}, {}, "mime"),
        ({"content-format": "none"}, {}, "none"),
        ({}, {"content-format": "plain"}, "plain"),
        ({}, {"content-format": "mime"}, "mime"),
        ({}, {"content-format": "none"}, "none"),
        ({"content-format": "plain"}, {"content-format": "mime"}, "plain"),
        ({"content-format": "mime"}, {"content-format": "plain"}, "mime"),
        ({"content-format": "none"}, {"content-format": "plain"}, "none"),
    ],
)
async def test_get_content_flag_resolution(tmp_path, project_flags, feature_flags, expected_format):
    """Test content-format-mime flag resolution and precedence."""
    category_dir = tmp_path / "docs"
    category_dir.mkdir()
    (category_dir / "README").write_text("# Test Content\n\nSome text.")

    project_data = Project(
        name="test",
        categories={"docs": Category(dir="docs", name="docs", patterns=["README", "guide"])},
        collections={},
    )

    result = await invoke_get_content(
        ContentArgs(expression="docs"),
        create_mock_session(tmp_path, project_data, project_flags, feature_flags),
    )
    assert result["success"] is True

    content = result["value"]

    if expected_format == "none":
        assert "# Test Content" in content
        assert "Some text." in content
        assert content.count("\n") >= 2
    elif expected_format == "plain":
        assert "# Test Content" in content
        assert "Some text." in content
    elif expected_format == "mime":
        assert "# Test Content" in content
        assert "Some text." in content


@pytest.mark.anyio
async def test_gather_valueerror_returns_validation_error(tmp_path, monkeypatch):
    """An escaping category dir raised in gather_content is a validation failure."""
    from mcp_guide.result_constants import ERROR_VALIDATION
    from mcp_guide.tools.tool_content import ContentArgs, internal_get_content

    async def boom(*_args, **_kwargs):
        raise ValueError("Document path must remain within the configured document root")

    monkeypatch.setattr("mcp_guide.tools.tool_content.gather_content", boom)
    project_data = Project(
        name="test",
        categories={"docs": Category(dir="docs", name="docs", patterns=["README"])},
        collections={},
    )
    result = await internal_get_content(
        ContentArgs(expression="docs"),
        await request_context_for(create_mock_session(tmp_path, project_data)),
    )
    assert result.success is False
    assert result.error_type == ERROR_VALIDATION
    assert "document root" in result.error
