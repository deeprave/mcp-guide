"""Tests for update tool."""

import pytest
from tests.helpers import create_unbound_test_session, request_context_for

from mcp_guide.tools.tool_update import UpdateDocumentsArgs, internal_update_documents


@pytest.mark.anyio
async def test_update_documents_propagates_docroot_resolution_error(runtime, monkeypatch):
    """Test update_documents returns a structured failure for docroot resolution issues."""
    context = await request_context_for(create_unbound_test_session(runtime))

    # Inject an unavailable configuration read at the I/O boundary.
    async def unavailable_docroot():
        raise OSError("docroot unavailable")

    monkeypatch.setattr(runtime, "get_docroot", unavailable_docroot)

    result = await internal_update_documents(UpdateDocumentsArgs(), context)

    assert result.success is False
    assert result.error_type == "config_read_error"
    assert "docroot unavailable" in result.error


@pytest.mark.anyio
@pytest.mark.parametrize("old_version", [None, "0.0.1"], ids=["new-docroot", "older-documents"])
async def test_update_installs_documents_and_version_then_skips_current(runtime, tmp_path, old_version):
    """The unbound tool performs real locked installation, then avoids a second update."""
    import yaml

    from mcp_guide import __version__
    from mcp_guide.tasks.update_task import McpUpdateTask

    docroot = tmp_path / "documents"
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    if old_version is not None:
        docroot.mkdir()
        (docroot / ".version").write_text(old_version)
    context = await request_context_for(create_unbound_test_session(runtime))
    if old_version is not None:
        (docroot / "_system").mkdir()
        (docroot / "_system" / "_update.mustache").write_text("Update documents now")
        task = context.session.task_manager.get_task_by_type(McpUpdateTask)
        # Stage the real startup prompt while the task remains subscribed.
        await task._prompt_update()
        assert not context.session.task_manager.is_queue_empty()
    result = await internal_update_documents(UpdateDocumentsArgs(), context)

    assert result.success, result.error
    assert result.value["updated"] is True
    assert result.value["stats"]["installed"] > 0
    assert (docroot / ".version").read_text() == __version__
    assert (docroot / ".original.zip").is_file()
    assert (docroot / "_system" / "_update.mustache").is_file()
    assert context.session.task_manager.is_queue_empty()
    again = await internal_update_documents(UpdateDocumentsArgs(), context)
    assert again.success
    assert again.value == {"message": f"Already at version {__version__}", "updated": False}
