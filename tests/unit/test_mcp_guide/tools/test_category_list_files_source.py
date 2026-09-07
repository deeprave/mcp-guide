"""Category file listing through real filesystem and document-store data."""

from dataclasses import replace

import pytest
import yaml
from pydantic import ValidationError
from tests.helpers import create_bound_test_session, request_context_for

from mcp_guide.models import Category
from mcp_guide.store.document_store import add_document
from mcp_guide.tools.tool_category import CategoryListFilesArgs, internal_category_list_files


def test_source_filter_rejects_invalid_value():
    """The advertised source constraint rejects unsupported filters."""
    with pytest.raises(ValidationError):
        CategoryListFilesArgs(category="docs", source="invalid")


@pytest.mark.anyio
async def test_source_and_name_filters_preserve_document_metadata(runtime, tmp_path, monkeypatch):
    """Default, explicit source and exact-name filtering expose the correct documents."""
    docroot = tmp_path / "docs"
    category_dir = docroot / "guidance"
    category_dir.mkdir(parents=True)
    (category_dir / "local.md").write_text("---\ndescription: Local guidance\n---\nLocal content")
    config = runtime.configuration_service().config_file
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    # Redirect only the database location; all persistence and discovery remain real.
    monkeypatch.setattr("mcp_guide.store.document_store.get_documents_db", lambda: tmp_path / "documents.db")
    session = await create_bound_test_session(runtime, "listing")
    await session.update_config(
        lambda project: replace(project, categories={"docs": Category(name="docs", dir="guidance", patterns=["*.txt"])})
    )
    context = await request_context_for(session)
    metadata = {"description": "Stored guidance", "type": "agent/information"}
    saved = await add_document("docs", "stored.md", "/client/stored.md", "file", "Stored content", metadata)
    await add_document("docs", "other.md", "/client/other.md", "file", "Other content")

    async def listed(**filters):
        result = await internal_category_list_files(CategoryListFilesArgs(category="docs", **filters), context)
        assert result.success, result
        return result.value

    combined = await listed()
    assert {(item["path"], item["source"]) for item in combined} == {
        ("local.md", "file"),
        ("stored.md", "store"),
        ("other.md", "store"),
    }
    files = await listed(source="files")
    assert len(files) == 1
    assert files[0]["path"] == "local.md"
    assert files[0]["description"] == "Local guidance"
    assert files[0]["size"] == (category_dir / "local.md").stat().st_size
    stored = await listed(source="stored")
    assert {item["path"] for item in stored} == {"stored.md", "other.md"}
    selected = await listed(source="stored", name="stored.md")
    assert selected == [next(item for item in combined if item["path"] == "stored.md")]
    assert saved.record is not None
    assert selected[0] == {
        "path": "stored.md",
        "basename": "stored.md",
        "size": 0,
        "source": "store",
        "description": "Stored guidance",
        "metadata": metadata,
        "source_type": "file",
        "source_path": "/client/stored.md",
        "created_at": saved.record.created_at,
        "updated_at": saved.record.updated_at,
    }
    assert await listed(name="stored") == []
    assert await listed(source="files", name="stored.md") == []
