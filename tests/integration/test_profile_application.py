"""Integration tests for profile application."""

import pytest
import pytest_asyncio

from mcp_guide.session import get_or_create_session, remove_current_session


@pytest.fixture(scope="module")
def enable_default_profile():
    """Enable default profile application for profile tests."""
    import mcp_guide.session

    original = mcp_guide.session._enable_default_profile
    mcp_guide.session._enable_default_profile = True
    yield
    mcp_guide.session._enable_default_profile = original


@pytest_asyncio.fixture
async def test_session(tmp_path, monkeypatch, enable_default_profile):
    """Create a test session."""
    # Set PWD to tmp_path to avoid picking up real project
    monkeypatch.setenv("PWD", str(tmp_path))

    # Mock resolve_project_name to return 'test'
    async def mock_resolve():
        return "test"

    monkeypatch.setattr("mcp_guide.session.resolve_project_name", mock_resolve)

    # Use get_or_create_session to properly register the session
    session = await get_or_create_session(project_name="test", _config_dir_for_tests=str(tmp_path))
    yield session
    await remove_current_session("test")


@pytest.mark.asyncio
class TestProfileApplication:
    """Tests for applying profiles to projects."""

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
            assert "test" in project.metadata.get("applied_profiles", [])
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
            assert project.metadata.get("applied_profiles") == ["profile1", "profile2"]
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

            # Apply profile second time
            result2 = await internal_use_project_profile(UseProjectProfileArgs(profile="test"), None)
            assert result2.success
            assert "already applied" in result2.value

            # Verify profile only listed once
            project = await test_session.get_project()
            assert project.metadata.get("applied_profiles") == ["test"]
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
            assert "not" in result.error.lower() and "found" in result.message.lower()
        finally:
            profile_module.get_profiles_dir = original_get_profiles_dir
