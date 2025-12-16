"""Tests for configuration migration from list-based to dict-based format."""

from mcp_guide.config import ConfigManager


class TestConfigMigration:
    """Tests for migrating list-based configuration to dict-based format."""

    def test_migrate_categories_list_to_dict(self):
        """Test migrating categories from list to dict format."""
        config_manager = ConfigManager()

        # Old list-based format
        old_data = {
            "categories": [
                {"name": "guide", "dir": "guide/", "patterns": ["guidelines"], "description": "Project guidelines"},
                {"name": "lang", "dir": "lang/", "patterns": ["python"], "description": "Language rules"},
            ]
        }

        migrated = config_manager._migrate_project_data(old_data)

        # Should be converted to dict format
        assert isinstance(migrated["categories"], dict)
        assert "guide" in migrated["categories"]
        assert "lang" in migrated["categories"]

        # Name should be removed from category data
        assert "name" not in migrated["categories"]["guide"]
        assert "name" not in migrated["categories"]["lang"]

        # Other fields should be preserved
        assert migrated["categories"]["guide"]["dir"] == "guide/"
        assert migrated["categories"]["guide"]["patterns"] == ["guidelines"]
        assert migrated["categories"]["guide"]["description"] == "Project guidelines"

    def test_migrate_collections_list_to_dict(self):
        """Test migrating collections from list to dict format."""
        config_manager = ConfigManager()

        # Old list-based format
        old_data = {
            "collections": [
                {"name": "all", "categories": ["guide", "lang"], "description": "All guidelines"},
                {"name": "review", "categories": ["guide"], "description": "Review only"},
            ]
        }

        migrated = config_manager._migrate_project_data(old_data)

        # Should be converted to dict format
        assert isinstance(migrated["collections"], dict)
        assert "all" in migrated["collections"]
        assert "review" in migrated["collections"]

        # Name should be removed from collection data
        assert "name" not in migrated["collections"]["all"]
        assert "name" not in migrated["collections"]["review"]

        # Other fields should be preserved
        assert migrated["collections"]["all"]["categories"] == ["guide", "lang"]
        assert migrated["collections"]["all"]["description"] == "All guidelines"

    def test_migrate_both_categories_and_collections(self):
        """Test migrating both categories and collections together."""
        config_manager = ConfigManager()

        # Old list-based format
        old_data = {
            "categories": [{"name": "guide", "dir": "guide/", "patterns": ["guidelines"]}],
            "collections": [{"name": "all", "categories": ["guide"], "description": "All"}],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
        }

        migrated = config_manager._migrate_project_data(old_data)

        # Both should be migrated
        assert isinstance(migrated["categories"], dict)
        assert isinstance(migrated["collections"], dict)

        # Other fields should be preserved
        assert migrated["created_at"] == "2023-01-01T00:00:00"
        assert migrated["updated_at"] == "2023-01-01T00:00:00"

    def test_migrate_already_dict_format_unchanged(self):
        """Test that already dict-based format is unchanged."""
        config_manager = ConfigManager()

        # Already dict-based format
        dict_data = {
            "categories": {"guide": {"dir": "guide/", "patterns": ["guidelines"]}},
            "collections": {"all": {"categories": ["guide"], "description": "All"}},
        }

        migrated = config_manager._migrate_project_data(dict_data)

        # Should be unchanged
        assert migrated == dict_data

    def test_migrate_empty_data(self):
        """Test migrating empty or missing categories/collections."""
        config_manager = ConfigManager()

        # Empty data
        empty_data = {}
        migrated = config_manager._migrate_project_data(empty_data)
        assert migrated == {}

        # Data with empty lists
        empty_lists = {"categories": [], "collections": []}
        migrated = config_manager._migrate_project_data(empty_lists)
        assert migrated["categories"] == {}
        assert migrated["collections"] == {}

    def test_migrate_preserves_original_data(self):
        """Test that migration doesn't modify the original data."""
        config_manager = ConfigManager()

        # Original data
        original_data = {"categories": [{"name": "guide", "dir": "guide/", "patterns": ["guidelines"]}]}

        # Keep a reference to the original
        original_categories = original_data["categories"]

        # Migrate
        migrated = config_manager._migrate_project_data(original_data)

        # Original should be unchanged
        assert original_data["categories"] is original_categories
        assert isinstance(original_data["categories"], list)
        assert original_data["categories"][0]["name"] == "guide"

        # Migrated should be different
        assert isinstance(migrated["categories"], dict)
        assert "guide" in migrated["categories"]
