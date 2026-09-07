"""Listener behaviour through real templates and delivered instructions."""

import pytest
import yaml
from tests.helpers import create_bound_test_session

from mcp_guide.guide_uri_listener import GuideUriListener
from mcp_guide.result import Result
from mcp_guide.startup_listener import StartupInstructionListener


@pytest.fixture
async def listener_session(runtime, tmp_path):
    docroot = tmp_path / "docs"
    system = docroot / "_system"
    system.mkdir(parents=True)
    config = runtime.configuration_service().config_file
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    session = await create_bound_test_session(runtime, "listeners")
    return session, system


@pytest.mark.anyio
@pytest.mark.parametrize("kind", ["guide", "startup"])
async def test_project_change_delivers_instructions_in_priority_order_without_config_replay(listener_session, kind):
    session, system = listener_session
    manager = session.task_manager
    await manager.queue_instruction("Already queued")
    if kind == "guide":
        listener = GuideUriListener()
        (system / "_guide-uri.mustache").write_text("Use guide URIs")
        expected = ["Already queued", "Use guide URIs"]
    else:
        listener = StartupInstructionListener()
        (system / "_startup.mustache").write_text("Start this project")
        (system / "_onboard_prompt.mustache").write_text("Onboard this project")
        expected = ["Start this project", "Already queued", "Onboard this project"]

    await listener.on_project_changed(session, "old", session.project_name)
    for content in expected:
        assert (await manager.process_result(Result.ok())).additional_agent_instructions == content
    assert manager.is_queue_empty()
    await listener.on_config_changed(session)
    assert manager.is_queue_empty()


@pytest.mark.anyio
@pytest.mark.parametrize("kind", ["guide", "startup"])
@pytest.mark.parametrize(
    "content", ["   ", "---\nrequires-never-enabled: true\n---\nHidden"], ids=["blank", "filtered"]
)
async def test_blank_or_requirement_filtered_templates_deliver_nothing(listener_session, kind, content):
    session, system = listener_session
    if kind == "guide":
        listener = GuideUriListener()
        patterns = ["_guide-uri"]
    else:
        listener = StartupInstructionListener()
        patterns = ["_startup", "_onboard_prompt"]
    for pattern in patterns:
        (system / f"{pattern}.mustache").write_text(content)
    await listener.on_project_changed(session, "old", session.project_name)
    assert (await session.task_manager.process_result(Result.ok())).additional_agent_instructions is None


@pytest.mark.anyio
@pytest.mark.parametrize("failure", ["missing", "unexpected"])
async def test_unavailable_startup_does_not_suppress_onboarding(listener_session, monkeypatch, failure):
    session, system = listener_session
    (system / "_onboard_prompt.mustache").write_text("Onboard this project")
    if failure == "unexpected":
        from mcp_guide.startup_listener import render_content

        # Inject the exceptional renderer boundary; normal rendering and queueing stay real.
        async def render_with_failure(session, *, pattern, category_dir):
            if pattern == "_startup":
                raise RuntimeError("Renderer unavailable")
            return await render_content(session, pattern=pattern, category_dir=category_dir)

        monkeypatch.setattr("mcp_guide.startup_listener.render_content", render_with_failure)

    await StartupInstructionListener().on_project_changed(session, "old", session.project_name)
    assert (
        await session.task_manager.process_result(Result.ok())
    ).additional_agent_instructions == "Onboard this project"
    assert session.task_manager.is_queue_empty()


@pytest.mark.anyio
@pytest.mark.parametrize("failure", ["missing", "unexpected"])
async def test_unavailable_guide_template_does_not_inject_instructions(listener_session, monkeypatch, failure):
    session, _ = listener_session
    if failure == "unexpected":
        # Exercise listener recovery from an unexpected renderer failure.
        async def fail_render(*args, **kwargs):
            raise RuntimeError("Renderer unavailable")

        monkeypatch.setattr("mcp_guide.guide_uri_listener.render_content", fail_render)
    await GuideUriListener().on_project_changed(session, "old", session.project_name)
    assert (await session.task_manager.process_result(Result.ok())).additional_agent_instructions is None
