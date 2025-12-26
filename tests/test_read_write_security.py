"""Tests for ReadWriteSecurityPolicy."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_guide.filesystem.read_write_security import ReadWriteSecurityPolicy, SecurityError


class TestReadWriteSecurityPolicy:
    """Test ReadWriteSecurityPolicy functionality."""

    def test_read_relative_path_allowed(self):
        """Test reading relative paths is allowed."""
        policy = ReadWriteSecurityPolicy()
        result = policy.validate_read_path("docs/readme.md")
        assert result == "docs/readme.md"

    def test_read_absolute_path_in_additional_paths(self):
        """Test reading from additional absolute paths is allowed."""
        policy = ReadWriteSecurityPolicy(additional_read_paths=["/shared/docs"])
        result = policy.validate_read_path("/shared/docs/file.txt")
        assert result == "/shared/docs/file.txt"

    def test_read_absolute_path_not_in_additional_paths(self):
        """Test reading from non-configured absolute paths is blocked."""
        policy = ReadWriteSecurityPolicy(additional_read_paths=["/shared/docs"])
        with pytest.raises(SecurityError, match="not in additional_read_paths"):
            policy.validate_read_path("/other/path/file.txt")

    def test_read_system_directory_blocked(self):
        """Test reading from system directories is blocked."""
        policy = ReadWriteSecurityPolicy(additional_read_paths=["/etc"])
        with pytest.raises(SecurityError, match="System directory access denied"):
            policy.validate_read_path("/etc/passwd")

    def test_write_relative_path_in_allowed_paths(self):
        """Test writing to allowed relative paths."""
        policy = ReadWriteSecurityPolicy(write_allowed_paths=["docs/", "output/"])
        result = policy.validate_write_path("docs/file.txt")
        assert result == "docs/file.txt"

    def test_write_relative_path_not_in_allowed_paths(self):
        """Test writing outside allowed paths is blocked."""
        policy = ReadWriteSecurityPolicy(write_allowed_paths=["docs/"])
        with pytest.raises(SecurityError, match="outside allowed write directories"):
            policy.validate_write_path("src/file.py")

    def test_write_absolute_path_blocked(self):
        """Test writing to absolute paths is blocked."""
        policy = ReadWriteSecurityPolicy(write_allowed_paths=["docs/"])
        with pytest.raises(SecurityError, match="Write to absolute path not allowed"):
            policy.validate_write_path("/home/user/file.txt")

    def test_write_temp_directory_allowed(self):
        """Test writing to safe temporary directories is allowed."""
        policy = ReadWriteSecurityPolicy()

        # Test various temp directory patterns
        temp_paths = ["/tmp/file.txt", "/var/tmp/data.json", "/private/tmp/cache.db", "~/.cache/app/data.txt"]

        for temp_path in temp_paths:
            with patch("mcp_guide.filesystem.temp_directories.is_safe_temp_path", return_value=True):
                result = policy.validate_write_path(temp_path)
                assert result == temp_path

    def test_path_traversal_prevention_read(self):
        """Test path traversal attacks are prevented for read operations."""
        policy = ReadWriteSecurityPolicy()
        with pytest.raises(SecurityError, match="Path traversal detected"):
            policy.validate_read_path("docs/../../../etc/passwd")

    def test_path_traversal_prevention_write(self):
        """Test path traversal attacks are prevented for write operations."""
        policy = ReadWriteSecurityPolicy(write_allowed_paths=["docs/"])
        with pytest.raises(SecurityError, match="Path traversal detected"):
            policy.validate_write_path("docs/../config.txt")

    def test_project_root_injection(self):
        """Test project root can be injected after initialization."""
        policy = ReadWriteSecurityPolicy()

        # Initially no project root
        assert policy.project_root is None

        # Inject project root
        policy.set_project_root("/home/user/project")
        assert policy.project_root == Path("/home/user/project")

    def test_read_absolute_path_within_project_root(self):
        """Test absolute path within project root is allowed when project root is set."""
        policy = ReadWriteSecurityPolicy()
        policy.set_project_root("/home/user/project")

        # Absolute path within project should be converted to relative and allowed
        result = policy.validate_read_path("/home/user/project/docs/file.md")
        assert result == "docs/file.md"

    def test_violation_count_tracking(self):
        """Test security violations are counted."""
        policy = ReadWriteSecurityPolicy(write_allowed_paths=["docs/"])

        assert policy.get_violation_count() == 0

        # Trigger violations
        with pytest.raises(SecurityError):
            policy.validate_write_path("src/file.py")
        assert policy.get_violation_count() == 1

        with pytest.raises(SecurityError):
            policy.validate_read_path("/etc/passwd")
        assert policy.get_violation_count() == 2

    def test_write_prefix_security_vulnerability_prevention(self):
        """Should prevent writes to directories with similar prefixes."""
        policy = ReadWriteSecurityPolicy(write_allowed_paths=["specs/"], additional_read_paths=[])

        # Should allow writes to specs/ directory
        result = policy.validate_write_path("specs/test.md")
        assert result == "specs/test.md"

        # Should NOT allow writes to specs2/ directory (security vulnerability)
        with pytest.raises(SecurityError) as exc_info:
            policy.validate_write_path("specs2/test.md")
        assert "outside allowed write directories" in str(exc_info.value)

        # Should NOT allow writes to specsheet/ directory
        with pytest.raises(SecurityError) as exc_info:
            policy.validate_write_path("specsheet/test.md")
        assert "outside allowed write directories" in str(exc_info.value)

    def test_empty_paths_handling(self):
        """Test handling of empty or None paths."""
        policy = ReadWriteSecurityPolicy()

        # Empty string becomes "." when normalized
        result = policy.validate_read_path("")
        assert result == "."

    def test_additional_read_paths_subdirectories(self):
        """Test subdirectories of additional read paths are accessible."""
        policy = ReadWriteSecurityPolicy(additional_read_paths=["/shared/docs"])

        # Subdirectory should be allowed
        result = policy.validate_read_path("/shared/docs/subdir/file.txt")
        assert result == "/shared/docs/subdir/file.txt"

        # Exact match should be allowed
        result = policy.validate_read_path("/shared/docs")
        assert result == "/shared/docs"


class TestSystemDirectoryBlacklist:
    """Test system directory blacklist functionality."""

    def test_unix_system_directories(self):
        """Test Unix system directories are blacklisted."""
        from mcp_guide.filesystem.system_directories import is_system_directory

        system_dirs = ["/etc", "/usr/bin", "/root", "/proc", "/sys"]
        for dir_path in system_dirs:
            assert is_system_directory(dir_path) is True

    def test_ssh_key_directories(self):
        """Test SSH key directories are blacklisted."""
        from mcp_guide.filesystem.system_directories import is_system_directory

        ssh_dirs = ["/home/user/.ssh", "/Users/user/.ssh", "/root/.ssh"]
        for dir_path in ssh_dirs:
            assert is_system_directory(dir_path) is True

    def test_windows_system_directories(self):
        """Test Windows system directories are blacklisted."""
        from mcp_guide.filesystem.system_directories import is_system_directory

        windows_dirs = ["C:\\Windows", "C:\\Program Files", "C:\\System32"]
        for dir_path in windows_dirs:
            assert is_system_directory(dir_path) is True

    def test_safe_directories_not_blacklisted(self):
        """Test safe directories are not blacklisted."""
        from mcp_guide.filesystem.system_directories import is_system_directory

        safe_dirs = ["/home/user/docs", "/tmp", "/var/tmp", "C:\\Users\\user\\Documents"]
        for dir_path in safe_dirs:
            assert is_system_directory(dir_path) is False


class TestTempDirectoryValidation:
    """Test temporary directory validation."""

    def test_tmp_directories_recognized(self):
        """Test tmp directories are recognized as safe."""
        from mcp_guide.filesystem.temp_directories import is_safe_temp_path

        tmp_paths = [
            Path("/tmp/file.txt"),
            Path("/var/tmp/data.json"),
            Path("/private/tmp/cache.db"),
            Path("~/project/tmp/output.txt"),
            Path("data/temp/processing.log"),
        ]

        for path in tmp_paths:
            assert is_safe_temp_path(path) is True

    def test_cache_directories_recognized(self):
        """Test cache directories are recognized as safe."""
        from mcp_guide.filesystem.temp_directories import is_safe_temp_path

        cache_paths = [Path("/home/user/.cache/app/data.txt"), Path("~/.cache/thumbnails/image.jpg")]

        for path in cache_paths:
            assert is_safe_temp_path(path) is True

    @patch.dict(os.environ, {"TMPDIR": "/custom/tmp", "TEMP": "C:\\CustomTemp"})
    def test_environment_variable_temp_paths(self):
        """Test environment variable temp paths are recognized."""
        from mcp_guide.filesystem.temp_directories import is_safe_temp_path

        # Test TMPDIR
        assert is_safe_temp_path(Path("/custom/tmp/file.txt")) is True

        # Test TEMP
        assert is_safe_temp_path(Path("C:\\CustomTemp\\data.json")) is True

    def test_non_temp_directories_rejected(self):
        """Test non-temporary directories are rejected."""
        from mcp_guide.filesystem.temp_directories import is_safe_temp_path

        non_temp_paths = [
            Path("/home/user/documents/file.txt"),
            Path("/usr/bin/program"),
            Path("src/main.py"),
            Path("/etc/config.conf"),
        ]

        for path in non_temp_paths:
            assert is_safe_temp_path(path) is False
