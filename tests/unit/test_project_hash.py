"""Tests for project hash utilities."""

import tempfile
from pathlib import Path

from mcp_guide.utils.project_hash import calculate_project_hash, extract_name_from_key, generate_project_key


class TestProjectHash:
    """Test project hash calculation and key generation."""

    def test_calculate_project_hash_consistency(self):
        """Hash calculation is consistent for same path."""
        path = "/home/user/my-project"
        hash1 = calculate_project_hash(path)
        hash2 = calculate_project_hash(path)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_calculate_project_hash_different_paths(self):
        """Different paths produce different hashes."""
        path1 = "/home/user/project1"
        path2 = "/home/user/project2"

        hash1 = calculate_project_hash(path1)
        hash2 = calculate_project_hash(path2)

        assert hash1 != hash2

    def test_calculate_project_hash_normalization(self):
        """Path normalization produces consistent hashes."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create paths with different representations
            path1 = str(Path(tmp_dir) / "project")
            path2 = str(Path(tmp_dir) / "." / "project")

            hash1 = calculate_project_hash(path1)
            hash2 = calculate_project_hash(path2)

            assert hash1 == hash2

    def test_generate_project_key(self):
        """Project key generation works correctly."""
        name = "my-project"
        hash_value = "abcdef1234567890" * 4  # 64 char hash

        key = generate_project_key(name, hash_value)

        assert key == "my-project-abcdef12"
        assert len(key.split("-")[-1]) == 8  # Short hash length

    def test_extract_name_from_key_new_format(self):
        """Name extraction works for hash-suffixed keys."""
        key = "my-project-abcdef12"
        name = extract_name_from_key(key)

        assert name == "my-project"

    def test_extract_name_from_key_legacy_format(self):
        """Name extraction works for legacy keys."""
        key = "my-project"
        name = extract_name_from_key(key)

        assert name == "my-project"

    def test_extract_name_from_key_complex_names(self):
        """Name extraction works for complex project names."""
        # Name with hyphens
        key = "my-complex-project-name-abcdef12"
        name = extract_name_from_key(key)

        assert name == "my-complex-project-name"

    def test_round_trip_key_generation(self):
        """Round trip: name -> key -> name works correctly."""
        original_name = "test-project"
        hash_value = "1234567890abcdef" * 4

        key = generate_project_key(original_name, hash_value)
        extracted_name = extract_name_from_key(key)

        assert extracted_name == original_name
