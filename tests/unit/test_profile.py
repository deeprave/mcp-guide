"""Tests for profile model."""

import pytest

import mcp_guide.models.profile as profile_module
from mcp_guide.models.profile import Profile


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

    def test_rejects_collection_without_categories(self):
        yaml_content = """
collections:
  - name: all
    categories: []
"""

        with pytest.raises(ValueError, match="must contain at least one category or expression"):
            Profile.from_yaml("test", yaml_content)

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


@pytest.mark.anyio
class TestProfileLoad:
    """Tests for Profile.load."""

    async def test_default_profile_provides_baseline_resource_content(self):
        profile = await Profile.load("_default")

        categories = {category.name: category for category in profile.categories}
        collections = {collection.name: collection for collection in profile.collections}

        assert categories["review"].patterns == ["general"]
        assert categories["checks"].patterns == ["instructions"]
        assert collections["code-review"].categories == ["review"]

    async def test_docker_and_shell_profiles_select_language_guidance(self):
        docker_profile = await Profile.load("docker")
        shell_profile = await Profile.load("shell")

        assert docker_profile.categories[0].name == "lang"
        assert docker_profile.categories[0].patterns == ["docker"]
        assert shell_profile.categories[0].name == "lang"
        assert shell_profile.categories[0].patterns == ["shell"]


@pytest.mark.anyio
class TestDiscoverProfiles:
    """Tests for discover_profiles."""

    async def test_discovery_excludes_internal_profiles_and_sorts_names(self, tmp_path, monkeypatch):
        profiles_dir = tmp_path / "_profiles"

        async def profiles_path():
            return profiles_dir

        monkeypatch.setattr(profile_module, "get_profiles_dir", profiles_path)
        assert await profile_module.discover_profiles() == []
        profiles_dir.mkdir()
        assert await profile_module.discover_profiles() == []
        for name in ("rust", "_default", "python"):
            (profiles_dir / f"{name}.yaml").write_text("categories: []")
        assert await profile_module.discover_profiles() == ["python", "rust"]

    async def test_discover_profiles_includes_docker_and_shell(self):
        profiles = await profile_module.discover_profiles()

        assert "docker" in profiles
        assert "shell" in profiles
        for name in ["_default", *profiles]:
            profile = await Profile.load(name)
            assert all(collection.categories for collection in profile.collections), name
