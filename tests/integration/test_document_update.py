"""Integration tests for document_update tool."""

from types import SimpleNamespace
from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from mcp_guide.tools.tool_document_update import DocumentUpdateArgs, internal_document_update


@pytest.fixture(scope="module")
def mcp_server(mcp_server_factory: Callable[[list[str]], Any]) -> Any:
    return mcp_server_factory(["tool_document_update"])


class TestDocumentUpdate:
    """Document update integration tests."""

    @pytest.mark.anyio
    async def test_rename(self, mcp_server: Any) -> None:
        mock_record = SimpleNamespace(category="docs", name="new.md", metadata={"type": "agent/instruction"})
        with patch("mcp_guide.tools.tool_document_update.update_document", new=AsyncMock(return_value=mock_record)):
            args = DocumentUpdateArgs(category="docs", name="old.md", new_name="new.md")
            result = await internal_document_update(args)
            assert result.success is True
            assert result.value["name"] == "new.md"

    @pytest.mark.anyio
    async def test_move_validates_category(self, mcp_server: Any) -> None:
        project = MagicMock()
        project.categories = {"docs": object()}
        session = AsyncMock()
        session.get_project = AsyncMock(return_value=project)

        with patch("mcp_guide.tools.tool_helpers.get_session", return_value=session):
            args = DocumentUpdateArgs(category="docs", name="file.md", new_category="nonexistent")
            result = await internal_document_update(args)
            assert result.success is False
            assert "does not exist" in result.error

    @pytest.mark.anyio
    async def test_not_found(self, mcp_server: Any) -> None:
        with patch("mcp_guide.tools.tool_document_update.update_document", new=AsyncMock(return_value=None)):
            args = DocumentUpdateArgs(category="docs", name="missing.md", new_name="x.md")
            result = await internal_document_update(args)
            assert result.success is False
            assert "not found" in result.error

    @pytest.mark.anyio
    async def test_collision_error(self, mcp_server: Any) -> None:
        with patch(
            "mcp_guide.tools.tool_document_update.update_document",
            new=AsyncMock(side_effect=ValueError("Document docs/b.md already exists")),
        ):
            args = DocumentUpdateArgs(category="docs", name="a.md", new_name="b.md")
            result = await internal_document_update(args)
            assert result.success is False
            assert "already exists" in result.error

    @pytest.mark.anyio
    async def test_metadata_add(self, mcp_server: Any) -> None:
        mock_record = SimpleNamespace(category="docs", name="file.md", metadata={"a": "1", "b": "2"})
        with patch("mcp_guide.tools.tool_document_update.update_document", new=AsyncMock(return_value=mock_record)):
            args = DocumentUpdateArgs(category="docs", name="file.md", metadata_add={"b": "2"})
            result = await internal_document_update(args)
            assert result.success is True
            assert result.value["metadata"] == {"a": "1", "b": "2"}

    @pytest.mark.anyio
    async def test_mutual_exclusivity_error(self, mcp_server: Any) -> None:
        with pytest.raises(ValidationError, match="mutually exclusive"):
            DocumentUpdateArgs(category="docs", name="file.md", metadata_add={"a": "1"}, metadata_clear=["b"])
