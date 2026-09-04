"""Integration tests for profile application."""

import re
from pathlib import Path

import pytest

import mcp_guide.session
from mcp_guide.discovery.commands import discover_commands
from mcp_guide.installer.core import get_templates_path
from mcp_guide.runtime import get_runtime
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content
from tests.helpers import create_test_session, request_context_for


@pytest.fixture(scope="module")
def enable_default_profile():
    """Enable default profile application for profile tests."""
    original = mcp_guide.session._enable_default_profile
    mcp_guide.session._enable_default_profile = True
    yield
    mcp_guide.session._enable_default_profile = original


@pytest.fixture
async def test_session(runtime, tmp_path, monkeypatch, enable_default_profile):
    """Create a test session."""
    # Set PWD to tmp_path to avoid picking up real project
    monkeypatch.setenv("PWD", str(tmp_path))

    # Build an isolated, explicitly bound session.
    session = await create_test_session(runtime, "test")

    async def get_bound_session_and_project(_ctx=None, *, session_id=None):
        return session, await session.get_project()

    monkeypatch.setattr(
        "mcp_guide.tools.tool_content.get_session_and_project",
        get_bound_session_and_project,
    )
    monkeypatch.setattr(
        "mcp_guide.tools.tool_project.get_session_and_project",
        get_bound_session_and_project,
    )
    yield session


@pytest.mark.anyio
class TestProfileApplication:
    """Tests for applying profiles to projects."""

    async def test_static_template_resources_render_with_default_profile(self, test_session):
        request_context = await request_context_for(test_session)
        await get_runtime().feature_flags().set("workflow", True)
        templates_path = await get_templates_path()
        resource_references = {
            match.group(1).strip()
            for template_path in Path(templates_path).rglob("*.mustache")
            for match in re.finditer(r"\{\{#resource\}\}([^{}]+)\{\{/resource\}\}", template_path.read_text())
        }
        commands_dir = Path(await get_runtime().get_docroot()) / "_commands"
        command_names = {command["name"] for command in await discover_commands(commands_dir, test_session)}

        for reference in resource_references:
            if reference.startswith("_"):
                command_name = reference.removeprefix("_").split("?", maxsplit=1)[0]
                assert command_name in command_names, reference
                continue

            result = await internal_get_content(ContentArgs(expression=reference, force=True), request_context)

            assert result.success, reference
            assert result.value.strip(), reference
            assert "No matching content found" not in result.value, reference

    async def test_docker_and_shell_profiles_render_language_guidance(self, test_session):
        from mcp_guide.tools.tool_project import UseProjectProfileArgs, internal_use_project_profile

        request_context = await request_context_for(test_session)
        for profile_name, heading in (("docker", "# Docker Guidelines"), ("shell", "# Shell Scripting Guidelines")):
            result = await internal_use_project_profile(UseProjectProfileArgs(profile=profile_name), request_context)
            assert result.success

            request_context = await request_context_for(test_session)
            content = await internal_get_content(ContentArgs(expression="lang", force=True), request_context)
            assert content.success
            assert heading in content.value

    async def test_apply_single_profile(self, test_session, tmp_path, monkeypatch):
        """Test applying a single profile to a project."""
        from mcp_guide.tools.tool_project import UseProjectProfileArgs, internal_use_project_profile

        # Set fake PWD to avoid picking up real project
        monkeypatch.setenv("PWD", str(tmp_path))

        # Create a test profile
        profiles_dir = tmp_path / "_profiles"
        profiles_dir.mkdir()
        profile_file = profiles_dir / "test.yaml"
        profile_file.write_text("""
categories:
  - name: docs
    dir: docs/
    patterns: []
    description: Documentation

collections:
  - name: all
    categories: [docs]
""")

        # Mock get_profiles_dir
        import mcp_guide.models.profile as profile_module

        original_get_profiles_dir = profile_module.get_profiles_dir

        async def mock_get_profiles_dir():
            return profiles_dir

        profile_module.get_profiles_dir = mock_get_profiles_dir

        try:
            # Apply profile
            args = UseProjectProfileArgs(profile="test")
            request_context = await request_context_for(test_session)
            result = await internal_use_project_profile(args, request_context)

            assert result.success
            assert "Applied profile 'test'" in result.value

            # Verify project has the category and collection
            project = await test_session.get_project()
            assert "docs" in project.categories
            assert "all" in project.collections
        finally:
            profile_module.get_profiles_dir = original_get_profiles_dir

    async def test_apply_multiple_profiles(self, test_session, tmp_path, monkeypatch):
        """Test applying multiple profiles to compose configuration."""
        from mcp_guide.tools.tool_project import UseProjectProfileArgs, internal_use_project_profile

        # Set fake PWD
        monkeypatch.setenv("PWD", str(tmp_path))

        # Create test profiles
        profiles_dir = tmp_path / "_profiles"
        profiles_dir.mkdir()

        (profiles_dir / "profile1.yaml").write_text("""
categories:
  - name: cat1
    dir: cat1/
    patterns: []
""")

        (profiles_dir / "profile2.yaml").write_text("""
categories:
  - name: cat2
    dir: cat2/
    patterns: []
""")

        # Mock get_profiles_dir
        import mcp_guide.models.profile as profile_module

        original_get_profiles_dir = profile_module.get_profiles_dir

        async def mock_get_profiles_dir():
            return profiles_dir

        profile_module.get_profiles_dir = mock_get_profiles_dir

        try:
            # Apply first profile
            request_context = await request_context_for(test_session)
            result1 = await internal_use_project_profile(UseProjectProfileArgs(profile="profile1"), request_context)
            assert result1.success

            # Apply second profile
            request_context = await request_context_for(test_session)
            result2 = await internal_use_project_profile(UseProjectProfileArgs(profile="profile2"), request_context)
            assert result2.success

            # Verify both categories exist
            project = await test_session.get_project()
            assert "cat1" in project.categories
            assert "cat2" in project.categories
        finally:
            profile_module.get_profiles_dir = original_get_profiles_dir

    async def test_apply_same_profile_twice_idempotent(self, test_session, tmp_path, monkeypatch):
        """Test that applying the same profile twice is idempotent."""
        from mcp_guide.tools.tool_project import UseProjectProfileArgs, internal_use_project_profile

        # Set fake PWD
        monkeypatch.setenv("PWD", str(tmp_path))

        # Create test profile
        profiles_dir = tmp_path / "_profiles"
        profiles_dir.mkdir()
        (profiles_dir / "test.yaml").write_text("""
categories:
  - name: docs
    dir: docs/
    patterns: []
""")

        # Mock get_profiles_dir
        import mcp_guide.models.profile as profile_module

        original_get_profiles_dir = profile_module.get_profiles_dir

        async def mock_get_profiles_dir():
            return profiles_dir

        profile_module.get_profiles_dir = mock_get_profiles_dir

        try:
            # Apply profile first time
            request_context = await request_context_for(test_session)
            result1 = await internal_use_project_profile(UseProjectProfileArgs(profile="test"), request_context)
            assert result1.success
            assert "Applied profile" in result1.value

            # Apply profile second time - should succeed (idempotent)
            request_context = await request_context_for(test_session)
            result2 = await internal_use_project_profile(UseProjectProfileArgs(profile="test"), request_context)
            assert result2.success
            assert "Applied profile" in result2.value

            # Verify category exists and wasn't duplicated
            project = await test_session.get_project()
            assert "docs" in project.categories
            assert len([c for c in project.categories if c == "docs"]) == 1
        finally:
            profile_module.get_profiles_dir = original_get_profiles_dir

    async def test_apply_invalid_profile(self, test_session, tmp_path, monkeypatch):
        """Test applying a non-existent profile."""
        from mcp_guide.tools.tool_project import UseProjectProfileArgs, internal_use_project_profile

        # Set fake PWD
        monkeypatch.setenv("PWD", str(tmp_path))

        # Create empty profiles directory
        profiles_dir = tmp_path / "_profiles"
        profiles_dir.mkdir()

        # Mock get_profiles_dir
        import mcp_guide.models.profile as profile_module

        original_get_profiles_dir = profile_module.get_profiles_dir

        async def mock_get_profiles_dir():
            return profiles_dir

        profile_module.get_profiles_dir = mock_get_profiles_dir

        try:
            # Try to apply non-existent profile
            request_context = await request_context_for(test_session)
            result = await internal_use_project_profile(UseProjectProfileArgs(profile="nonexistent"), request_context)
            assert not result.success
            assert "not" in result.message.lower() and "found" in result.message.lower()
        finally:
            profile_module.get_profiles_dir = original_get_profiles_dir
