"""Integration tests for isolated profile application."""

import pytest

import mcp_guide.session
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

    yield session


@pytest.mark.anyio
class TestProfileApplication:
    """Tests for applying profiles to projects."""

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
