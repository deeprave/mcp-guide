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

PROFILE_SOURCE_DIRECTORY = Path(__file__).parents[2] / "src" / "mcp_guide" / "templates" / "_profiles"
BUNDLED_PROFILE_NAMES = tuple(
    profile_path.stem
    for profile_path in sorted(PROFILE_SOURCE_DIRECTORY.glob("*.yaml"))
    if not profile_path.stem.startswith("_")
)


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

    async def test_swift_platform_and_test_profiles_compose(self, test_session):
        from mcp_guide.tools.tool_project import UseProjectProfileArgs, internal_use_project_profile

        for profile_name in ("swift", "swiftui", "ios", "xctest"):
            result = await internal_use_project_profile(
                UseProjectProfileArgs(profile=profile_name), await request_context_for(test_session)
            )
            assert result.success, profile_name

        request_context = await request_context_for(test_session)
        language = await internal_get_content(ContentArgs(expression="lang", force=True), request_context)
        checks = await internal_get_content(ContentArgs(expression="checks", force=True), request_context)

        assert language.success
        assert "# Swift Guidelines" in language.value
        assert "# SwiftUI Guidelines" in language.value
        assert "# iOS Build Guidance" in language.value
        assert checks.success
        assert "# Swift iOS Testing" in checks.value
        assert "# XCTest Guidance" in checks.value

    async def test_testing_profile_renders_general_testing_guidance(self, test_session):
        from mcp_guide.tools.tool_project import UseProjectProfileArgs, internal_use_project_profile

        result = await internal_use_project_profile(
            UseProjectProfileArgs(profile="testing"), await request_context_for(test_session)
        )

        assert result.success
        checks = await internal_get_content(
            ContentArgs(expression="checks", force=True), await request_context_for(test_session)
        )
        assert checks.success
        assert "These are the guidelines to follow for general code and quality testing." in checks.value

    @pytest.mark.parametrize("profile_name", BUNDLED_PROFILE_NAMES)
    async def test_bundled_profiles_render_their_declared_guidance(self, test_session, profile_name):
        from mcp_guide.models.profile import Profile
        from mcp_guide.tools.tool_project import UseProjectProfileArgs, internal_use_project_profile

        result = await internal_use_project_profile(
            UseProjectProfileArgs(profile=profile_name), await request_context_for(test_session)
        )

        assert result.success, profile_name
        profile = await Profile.load(profile_name)
        project = await test_session.get_project()
        for category in profile.categories:
            assert set(category.patterns) <= set(project.categories[category.name].patterns)
            for pattern in category.patterns:
                content = await internal_get_content(
                    ContentArgs(expression=category.name, pattern=pattern, force=True),
                    await request_context_for(test_session),
                )
                assert content.success, f"{profile_name}: {category.name}/{pattern}"
                assert "No matching content found" not in content.value, f"{profile_name}: {category.name}/{pattern}"
                assert content.value.strip(), f"{profile_name}: {category.name}/{pattern}"

    async def test_profiles_compose_idempotently_and_report_missing(self, test_session, tmp_path, monkeypatch):
        """Real profile files compose categories/collections and persist without duplicates."""
        import yaml

        from mcp_guide.tools.tool_project import UseProjectProfileArgs, internal_use_project_profile

        profiles_dir = tmp_path / "_profiles"
        profiles_dir.mkdir()
        (profiles_dir / "first.yaml").write_text(
            yaml.safe_dump(
                {
                    "categories": [
                        {"name": "custom-docs", "dir": "docs/", "patterns": ["*.md"], "description": "Documentation"}
                    ],
                    "collections": [{"name": "custom-all", "categories": ["custom-docs"]}],
                }
            )
        )
        (profiles_dir / "second.yaml").write_text(
            yaml.safe_dump(
                {
                    "categories": [{"name": "custom-api", "dir": "api/", "patterns": ["*.py"]}],
                }
            )
        )

        # Substitute only the packaged resource location; parsing and application remain real.
        async def profile_directory():
            return profiles_dir

        monkeypatch.setattr("mcp_guide.models.profile.get_profiles_dir", profile_directory)

        async def apply(name):
            return await internal_use_project_profile(
                UseProjectProfileArgs(profile=name), await request_context_for(test_session)
            )

        first = await apply("first")
        assert first.success
        assert "Applied profile 'first'" in first.value
        assert (await apply("second")).success
        combined = await test_session.get_project()
        assert combined.categories["custom-docs"].patterns == ["*.md"]
        assert combined.categories["custom-api"].patterns == ["*.py"]
        assert combined.collections["custom-all"].categories == ["custom-docs"]
        assert (await apply("first")).success
        assert await test_session.get_project() == combined
        missing = await apply("nonexistent")
        assert not missing.success
        assert "not found" in missing.message.lower()
        assert await test_session.get_project() == combined

    async def test_profile_application_rejects_invalid_and_escaping_profile_sources(
        self, test_session, tmp_path, monkeypatch
    ):
        from mcp_guide.result_constants import ERROR_INVALID_NAME
        from mcp_guide.tools.tool_project import (
            ShowProfileArgs,
            UseProjectProfileArgs,
            internal_show_profile,
            internal_use_project_profile,
        )

        profiles_dir = tmp_path / "_profiles"
        profiles_dir.mkdir()
        outside_profile = tmp_path / "outside.yaml"
        outside_profile.write_text("categories: []")
        (profiles_dir / "escape.yaml").symlink_to(outside_profile)

        async def profile_directory():
            return profiles_dir

        monkeypatch.setattr("mcp_guide.models.profile.get_profiles_dir", profile_directory)

        async def apply(name):
            return await internal_use_project_profile(
                UseProjectProfileArgs(profile=name), await request_context_for(test_session)
            )

        for name in ("../outside", "escape"):
            application_result = await apply(name)
            inspection_result = await internal_show_profile(
                ShowProfileArgs(profile=name), await request_context_for(test_session)
            )

            for result in (application_result, inspection_result):
                assert not result.success
                assert result.error_type == ERROR_INVALID_NAME
                assert "outside.yaml" not in (result.error or "")
