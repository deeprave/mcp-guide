"""Tests for profile model."""

import pytest

from mcp_guide.models.profile import Profile


@pytest.fixture(scope="module")
def enable_default_profile():
    """Enable default profile application for profile tests."""
    import mcp_guide.session

    original = mcp_guide.session._enable_default_profile
    mcp_guide.session._enable_default_profile = True
    yield
    mcp_guide.session._enable_default_profile = original


class TestProfileFromYaml:
    """Tests for Profile.from_yaml."""

    def test_load_valid_profile(self):
        """Test loading a valid profile."""
        yaml_content = """
categories:
  - name: docs
    dir: docs/
    patterns: []
    description: Documentation

collections:
  - name: all
    categories: [docs]
    description: All docs
"""
        profile = Profile.from_yaml("test", yaml_content)

        assert profile.name == "test"
        assert len(profile.categories) == 1
        assert profile.categories[0].name == "docs"
        assert profile.categories[0].dir == "docs/"
        assert len(profile.collections) == 1
        assert profile.collections[0].name == "all"

    def test_profile_with_only_categories(self):
        """Test profile with only categories."""
        yaml_content = """
categories:
  - name: docs
    dir: docs/
    patterns: []
"""
        profile = Profile.from_yaml("test", yaml_content)

        assert len(profile.categories) == 1
        assert len(profile.collections) == 0

    def test_profile_with_only_collections(self):
        """Test profile with only collections."""
        yaml_content = """
collections:
  - name: all
    categories: [docs]
"""
        profile = Profile.from_yaml("test", yaml_content)

        assert len(profile.categories) == 0
        assert len(profile.collections) == 1

    def test_empty_profile(self):
        """Test empty profile."""
        yaml_content = "{}"
        profile = Profile.from_yaml("test", yaml_content)

        assert len(profile.categories) == 0
        assert len(profile.collections) == 0

    def test_invalid_yaml_not_dict(self):
        """Test that non-dict YAML raises ValueError."""
        yaml_content = "- item1\n- item2"

        with pytest.raises(ValueError, match="must be a YAML dictionary"):
            Profile.from_yaml("test", yaml_content)

    def test_unsupported_fields(self):
        """Test that unsupported fields raise ValueError."""
        yaml_content = """
categories:
  - name: docs
    dir: docs/
    patterns: []
unsupported_field: value
"""
        with pytest.raises(ValueError, match="unsupported fields"):
            Profile.from_yaml("test", yaml_content)


@pytest.mark.asyncio
class TestProfileLoad:
    """Tests for Profile.load."""

    async def test_load_nonexistent_profile(self, tmp_path):
        """Test loading a profile that doesn't exist."""
        from mcp_guide.models.profile import Profile

        # Create empty profiles directory
        profiles_dir = tmp_path / "_profiles"
        profiles_dir.mkdir()

        # Mock get_profiles_dir to return our temp directory
        import mcp_guide.models.profile as profile_module

        original_get_profiles_dir = profile_module.get_profiles_dir

        async def mock_get_profiles_dir():
            return profiles_dir

        profile_module.get_profiles_dir = mock_get_profiles_dir

        try:
            with pytest.raises(FileNotFoundError, match="Profile 'nonexistent' not found"):
                await Profile.load("nonexistent")
        finally:
            profile_module.get_profiles_dir = original_get_profiles_dir

    async def test_load_existing_profile(self, tmp_path):
        """Test loading an existing profile."""
        from mcp_guide.models.profile import Profile

        # Create profiles directory with a profile
        profiles_dir = tmp_path / "_profiles"
        profiles_dir.mkdir()
        profile_file = profiles_dir / "python.yaml"
        profile_file.write_text("""
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
            profile = await Profile.load("python")
            assert profile.name == "python"
            assert len(profile.categories) == 1
        finally:
            profile_module.get_profiles_dir = original_get_profiles_dir


@pytest.mark.asyncio
class TestDiscoverProfiles:
    """Tests for discover_profiles."""

    async def test_discover_empty_directory(self, tmp_path):
        """Test discovering profiles in empty directory."""
        from mcp_guide.models.profile import discover_profiles

        profiles_dir = tmp_path / "_profiles"
        profiles_dir.mkdir()

        import mcp_guide.models.profile as profile_module

        original_get_profiles_dir = profile_module.get_profiles_dir

        async def mock_get_profiles_dir():
            return profiles_dir

        profile_module.get_profiles_dir = mock_get_profiles_dir

        try:
            profiles = await discover_profiles()
            assert profiles == []
        finally:
            profile_module.get_profiles_dir = original_get_profiles_dir

    async def test_discover_profiles_excludes_underscore(self, tmp_path):
        """Test that profiles starting with underscore are excluded."""
        from mcp_guide.models.profile import discover_profiles

        profiles_dir = tmp_path / "_profiles"
        profiles_dir.mkdir()
        (profiles_dir / "python.yaml").write_text("categories: []")
        (profiles_dir / "_default.yaml").write_text("categories: []")
        (profiles_dir / "rust.yaml").write_text("categories: []")

        import mcp_guide.models.profile as profile_module

        original_get_profiles_dir = profile_module.get_profiles_dir

        async def mock_get_profiles_dir():
            return profiles_dir

        profile_module.get_profiles_dir = mock_get_profiles_dir

        try:
            profiles = await discover_profiles()
            assert sorted(profiles) == ["python", "rust"]
        finally:
            profile_module.get_profiles_dir = original_get_profiles_dir
