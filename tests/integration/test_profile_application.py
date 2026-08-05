"""Integration tests for profile application."""

import re
from pathlib import Path

import pytest

import mcp_guide.session
from mcp_guide.discovery.commands import discover_commands
from mcp_guide.installer.core import get_templates_path
from mcp_guide.session import get_session, remove_current_session
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content


@pytest.fixture(scope="module")
def enable_default_profile():
    """Enable default profile application for profile tests."""
    original = mcp_guide.session._enable_default_profile
    mcp_guide.session._enable_default_profile = True
    yield
    mcp_guide.session._enable_default_profile = original


@pytest.fixture
async def test_session(tmp_path, monkeypatch, enable_default_profile):
    """Create a test session."""
    # Set PWD to tmp_path to avoid picking up real project
    monkeypatch.setenv("PWD", str(tmp_path))

    # Mock resolve_project_name to return 'test'
    async def mock_resolve():
        return "test"

    monkeypatch.setattr("mcp_guide.session.resolve_project_name", mock_resolve)

    # Use get_session to properly register the session
    session = await get_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    yield session
    await remove_current_session()


@pytest.mark.anyio
class TestProfileApplication:
    """Tests for applying profiles to projects."""

    async def test_static_template_resources_render_with_default_profile(self, test_session):
        await test_session.feature_flags().set("workflow", True)
        templates_path = await get_templates_path()
        resource_references = {
            match.group(1).strip()
            for template_path in Path(templates_path).rglob("*.mustache")
            for match in re.finditer(r"\{\{#resource\}\}([^{}]+)\{\{/resource\}\}", template_path.read_text())
        }
        commands_dir = Path(await test_session.get_docroot()) / "_commands"
        command_names = {command["name"] for command in await discover_commands(commands_dir)}

        for reference in resource_references:
            if reference.startswith("_"):
                command_name = reference.removeprefix("_").split("?", maxsplit=1)[0]
                assert command_name in command_names, reference
                continue

            result = await internal_get_content(ContentArgs(expression=reference, force=True))

            assert result.success, reference
            assert result.value.strip(), reference
            assert "No matching content found" not in result.value, reference

    async def test_docker_and_shell_profiles_render_language_guidance(self, test_session):
        from mcp_guide.tools.tool_project import UseProjectProfileArgs, internal_use_project_profile

        for profile_name, heading in (("docker", "# Docker Guidelines"), ("shell", "# Shell Scripting Guidelines")):
            result = await internal_use_project_profile(UseProjectProfileArgs(profile=profile_name))
            assert result.success

            content = await internal_get_content(ContentArgs(expression="lang", force=True))
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
            result = await internal_use_project_profile(args, None)

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
            result1 = await internal_use_project_profile(UseProjectProfileArgs(profile="profile1"), None)
            assert result1.success

            # Apply second profile
            result2 = await internal_use_project_profile(UseProjectProfileArgs(profile="profile2"), None)
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
            result1 = await internal_use_project_profile(UseProjectProfileArgs(profile="test"), None)
            assert result1.success
            assert "Applied profile" in result1.value

            # Apply profile second time - should succeed (idempotent)
            result2 = await internal_use_project_profile(UseProjectProfileArgs(profile="test"), None)
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
            result = await internal_use_project_profile(UseProjectProfileArgs(profile="nonexistent"), None)
            assert not result.success
            assert "not" in result.message.lower() and "found" in result.message.lower()
        finally:
            profile_module.get_profiles_dir = original_get_profiles_dir
