"""Startup document-update prompts use real flags, version files and rendering."""

import pytest
import yaml
from tests.helpers import create_unbound_test_session

from mcp_guide.task_manager import EventType
from mcp_guide.tasks.update_task import StartupTask


@pytest.mark.anyio
@pytest.mark.anyio
async def test_development_mode_skips_startup_update_prompt(runtime, tmp_path):
    """Development docroots are read directly and must not receive installer metadata."""
    docroot = tmp_path / "documents"
    (docroot / "_system").mkdir(parents=True)
    (docroot / "_system" / "_update.mustache").write_text("Update documents now")
    (docroot / ".version").write_text("0.0.1")
    runtime.configuration_service().config_file.write_text(
        yaml.safe_dump(
            {
                "docroot": str(docroot),
                "feature_flags": {"autoupdate": True, "guide-development": True},
                "projects": {},
            }
        ),
        encoding="utf-8",
    )
    session = create_unbound_test_session(runtime)
    task = session.task_manager.get_task_by_type(StartupTask)
    assert task is not None

    result = await task.handle_event(EventType.TIMER_ONCE, {})

    assert result.result
    assert session.task_manager.is_queue_empty()
    assert session.task_manager.get_task_by_type(StartupTask) is None


@pytest.mark.anyio
@pytest.mark.parametrize("missing", [False, True], ids=["unsafe-docroot", "missing-package"])
async def test_unavailable_template_source_prevents_prompt(runtime, tmp_path, monkeypatch, missing):
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    (tmp_path / ".version").write_text("0.0.1")

    # Control package location, leaving actual docroot validation in place.
    async def package_templates():
        if missing:
            raise FileNotFoundError("Templates directory not found")
        return tmp_path

    monkeypatch.setattr("mcp_guide.installer.core.get_templates_path", package_templates)
    session = create_unbound_test_session(runtime)
    task = session.task_manager.get_task_by_type(StartupTask)
    assert task is not None
    result = await task.handle_event(EventType.TIMER_ONCE, {})
    assert result.result
    assert session.task_manager.is_queue_empty()
    assert session.task_manager.get_task_by_type(StartupTask) is None
