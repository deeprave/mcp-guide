"""Tests for core installer functionality."""

import hashlib
from pathlib import Path
from zipfile import ZipFile

import pytest

from mcp_guide.installer.core import (
    apply_diff,
    compare_files,
    compute_diff,
    compute_file_hash,
    create_archive,
    extract_from_archive,
    file_exists_in_archive,
)


class TestFileHashing:
    """Tests for file hashing functionality."""

    @pytest.mark.asyncio
    async def test_compute_file_hash_returns_sha256_hex_digest(self, tmp_path: Path) -> None:
        """Test that compute_file_hash returns SHA256 hex digest of file content."""
        # Arrange
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        expected_hash = hashlib.sha256(content).hexdigest()

        # Act
        result = await compute_file_hash(test_file)

        # Assert
        assert result == expected_hash

    @pytest.mark.asyncio
    async def test_compare_files_returns_true_for_identical_files(self, tmp_path: Path) -> None:
        """Test that compare_files returns True when files have identical content."""
        # Arrange
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        content = b"Same content"
        file1.write_bytes(content)
        file2.write_bytes(content)

        # Act
        result = await compare_files(file1, file2)

        # Assert
        assert result is True


class TestArchiveOperations:
    """Tests for zip archive operations."""

    @pytest.mark.asyncio
    async def test_create_archive_stores_files_in_zip(self, tmp_path: Path) -> None:
        """Test that create_archive stores files in a zip archive."""
        # Arrange
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        file1 = source_dir / "file1.txt"
        file1.write_text("Content 1")
        file2 = source_dir / "file2.txt"
        file2.write_text("Content 2")

        archive_path = tmp_path / "archive.zip"
        files = [file1, file2]

        # Act
        await create_archive(archive_path, files, source_dir)

        # Assert
        assert archive_path.exists()
        with ZipFile(archive_path, "r") as zf:
            assert "file1.txt" in zf.namelist()
            assert "file2.txt" in zf.namelist()
            assert zf.read("file1.txt").decode() == "Content 1"
            assert zf.read("file2.txt").decode() == "Content 2"

    @pytest.mark.asyncio
    async def test_create_archive_includes_readme(self, tmp_path: Path) -> None:
        """Test that create_archive includes a README.md explaining the archive."""
        # Arrange
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        file1 = source_dir / "file1.txt"
        file1.write_text("content1")

        archive_path = tmp_path / "test.zip"

        # Act
        await create_archive(archive_path, [file1], source_dir)

        # Assert
        with ZipFile(archive_path, "r") as zf:
            names = zf.namelist()
            assert "README.md" in names
            readme_content = zf.read("README.md").decode()
            assert "original files" in readme_content.lower()
            assert "do not modify" in readme_content.lower()

    @pytest.mark.asyncio
    async def test_extract_from_archive_retrieves_file_content(self, tmp_path: Path) -> None:
        """Test that extract_from_archive retrieves file content from zip."""
        # Arrange
        archive_path = tmp_path / "archive.zip"
        with ZipFile(archive_path, "w") as zf:
            zf.writestr("test.txt", "Test content")

        # Act
        content = await extract_from_archive(archive_path, "test.txt")

        # Assert
        assert content == b"Test content"

    @pytest.mark.asyncio
    async def test_file_exists_in_archive_returns_true_when_present(self, tmp_path: Path) -> None:
        """Test that file_exists_in_archive returns True when file is in archive."""
        # Arrange
        archive_path = tmp_path / "archive.zip"
        with ZipFile(archive_path, "w") as zf:
            zf.writestr("present.txt", "content")

        # Act
        result = await file_exists_in_archive(archive_path, "present.txt")

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_file_exists_in_archive_returns_false_when_absent(self, tmp_path: Path) -> None:
        """Test that file_exists_in_archive returns False when file is not in archive."""
        # Arrange
        archive_path = tmp_path / "archive.zip"
        with ZipFile(archive_path, "w") as zf:
            zf.writestr("other.txt", "content")

        # Act
        result = await file_exists_in_archive(archive_path, "missing.txt")

        # Assert
        assert result is False


class TestDiffOperations:
    """Tests for diff computation and application."""

    @pytest.mark.asyncio
    async def test_compute_diff_generates_unified_diff(self, tmp_path: Path) -> None:
        """Test that compute_diff generates unified diff between two files."""
        # Arrange
        original = tmp_path / "original.txt"
        original.write_text("Line 1\nLine 2\nLine 3\n")
        current = tmp_path / "current.txt"
        current.write_text("Line 1\nLine 2 modified\nLine 3\n")

        # Act
        diff = await compute_diff(original, current)

        # Assert
        assert diff is not None
        assert "-Line 2" in diff
        assert "+Line 2 modified" in diff

    @pytest.mark.asyncio
    async def test_apply_diff_successfully_patches_file(self, tmp_path: Path) -> None:
        """Test that apply_diff successfully applies a diff to a target file."""
        # Arrange
        target = tmp_path / "target.txt"
        target.write_text("Line 1\nLine 2\nLine 3\n")

        # Create a diff with absolute paths (apply_diff should rewrite them)
        diff_content = """--- /some/absolute/path/original.txt
+++ /another/absolute/path/modified.txt
@@ -1,3 +1,3 @@
 Line 1
-Line 2
+Line 2 modified
 Line 3
"""

        # Act
        success = await apply_diff(target, diff_content)

        # Assert
        assert success is True
        assert target.read_text() == "Line 1\nLine 2 modified\nLine 3\n"

    @pytest.mark.asyncio
    async def test_apply_diff_returns_false_when_patch_fails(self, tmp_path: Path) -> None:
        """Test that apply_diff returns False when patch cannot be applied."""
        # Arrange
        target = tmp_path / "target.txt"
        target.write_text("Line 1\nDifferent content\nLine 3\n")

        # Create a diff that won't match the file content
        diff_content = """--- original.txt
+++ modified.txt
@@ -1,3 +1,3 @@
 Line 1
-Line 2
+Line 2 modified
 Line 3
"""

        # Act
        success = await apply_diff(target, diff_content)

        # Assert
        assert success is False


class TestSmartUpdate:
    """Tests for smart update logic."""

    @pytest.mark.asyncio
    async def test_smart_update_skips_when_current_equals_new(self, tmp_path: Path) -> None:
        """Test that smart_update skips installation when current file equals new file."""
        # Arrange
        from mcp_guide.installer.core import smart_update

        current = tmp_path / "current.txt"
        new = tmp_path / "new.txt"
        original = tmp_path / "original.txt"

        content = "Same content\n"
        current.write_text(content)
        new.write_text(content)
        original.write_text("Different original\n")

        # Act
        result = await smart_update(current, new, original)

        # Assert
        assert result["action"] == "skipped"
        assert result["reason"] == "current equals new"
        assert current.read_text() == content  # Unchanged

    @pytest.mark.asyncio
    async def test_smart_update_replaces_when_current_equals_original(self, tmp_path: Path) -> None:
        """Test that smart_update replaces file when current equals original (no user changes)."""
        # Arrange
        from mcp_guide.installer.core import smart_update

        current = tmp_path / "current.txt"
        new = tmp_path / "new.txt"
        original = tmp_path / "original.txt"

        original_content = "Original content\n"
        new_content = "New content\n"

        current.write_text(original_content)
        new.write_text(new_content)
        original.write_text(original_content)

        # Act
        result = await smart_update(current, new, original)

        # Assert
        assert result["action"] == "replaced"
        assert result["reason"] == "no user changes"
        assert current.read_text() == new_content

    @pytest.mark.asyncio
    async def test_smart_update_patches_with_backup_when_user_modified(self, tmp_path: Path) -> None:
        """Test that smart_update backs up and patches when user has modified file."""
        # Arrange
        from mcp_guide.installer.core import smart_update

        current = tmp_path / "current.txt"
        new = tmp_path / "new.txt"
        original = tmp_path / "original.txt"

        # User added line 4, new version modifies line 2 (non-conflicting)
        original.write_text("Line 1\nLine 2\nLine 3\n")
        current.write_text("Line 1\nLine 2\nLine 3\nLine 4 user added\n")
        new.write_text("Line 1\nLine 2 updated\nLine 3\n")

        # Act
        result = await smart_update(current, new, original)

        # Assert
        assert result["action"] == "patched"
        assert result["reason"] == "user changes preserved"
        assert current.read_text() == "Line 1\nLine 2 updated\nLine 3\nLine 4 user added\n"

        # Verify backup was created
        backup = tmp_path / "current.txt.orig"
        assert backup.exists()
        assert backup.read_text() == "Line 1\nLine 2\nLine 3\nLine 4 user added\n"

    @pytest.mark.asyncio
    async def test_smart_update_backs_up_and_warns_when_patch_fails(self, tmp_path: Path) -> None:
        """Test that smart_update backs up and warns when patch cannot be applied."""
        # Arrange
        from mcp_guide.installer.core import smart_update

        current = tmp_path / "current.txt"
        new = tmp_path / "new.txt"
        original = tmp_path / "original.txt"

        # User modified line 2, new version also modifies line 2 (conflicting)
        original.write_text("Line 1\nLine 2\nLine 3\n")
        current.write_text("Line 1\nLine 2 user edit\nLine 3\n")
        new.write_text("Line 1\nLine 2 updated\nLine 3\n")

        # Act
        result = await smart_update(current, new, original)

        # Assert
        assert result["action"] == "conflict"
        assert result["reason"] == "patch failed"
        # Current file is restored to original user content
        assert current.read_text() == "Line 1\nLine 2 user edit\nLine 3\n"

        # No backup file created since current already has the user's content
        backup = tmp_path / "current.txt.orig"
        assert not backup.exists()

    @pytest.mark.asyncio
    async def test_smart_update_replaces_when_original_missing(self, tmp_path: Path) -> None:
        """Test that smart_update replaces file when original doesn't exist (can't track changes)."""
        # Arrange
        from mcp_guide.installer.core import smart_update

        current = tmp_path / "current.txt"
        new = tmp_path / "new.txt"
        original = tmp_path / "original.txt"  # Does not exist

        current.write_text("Current content\n")
        new.write_text("New content\n")

        # Act
        result = await smart_update(current, new, original)

        # Assert
        assert result["action"] == "replaced"
        assert result["reason"] == "no original to compare"
        assert current.read_text() == "New content\n"

        # No backup should be created (can't determine if user modified)
        backup = tmp_path / "current.txt.orig"
        assert not backup.exists()


class TestTemplateDiscovery:
    """Tests for template discovery."""

    @pytest.mark.asyncio
    async def test_get_templates_path_returns_package_directory(self) -> None:
        """Test that get_templates_path returns the templates directory from package."""
        # Arrange
        from mcp_guide.installer.core import get_templates_path

        # Act
        templates_path = await get_templates_path()

        # Assert
        assert templates_path.exists()
        assert templates_path.is_dir()
        assert templates_path.name == "templates"

    @pytest.mark.asyncio
    async def test_list_template_files_returns_all_files(self) -> None:
        """Test that list_template_files returns all files recursively."""
        # Arrange
        from mcp_guide.installer.core import list_template_files

        # Act
        files = await list_template_files()

        # Assert
        assert len(files) > 0
        assert all(isinstance(f, Path) for f in files)
        assert all(f.is_file() for f in files)
        # Verify no dot-prefixed files are included
        assert all(not f.name.startswith(".") for f in files)


class TestFileInstallation:
    """Tests for file installation."""

    @pytest.mark.asyncio
    async def test_install_file_creates_directories(self, tmp_path: Path) -> None:
        """Test that install_file creates parent directories if needed."""
        # Arrange
        from mcp_guide.installer.core import install_file

        source = tmp_path / "source.txt"
        source.write_text("content")

        dest = tmp_path / "nested" / "dir" / "dest.txt"

        # Act
        await install_file(source, dest)

        # Assert
        assert dest.exists()
        assert dest.read_text() == "content"
        assert dest.parent.exists()

    @pytest.mark.asyncio
    async def test_install_directory_copies_tree(self, tmp_path: Path) -> None:
        """Test that install_directory copies entire directory tree."""
        # Arrange
        from mcp_guide.installer.core import install_directory

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "subdir").mkdir()
        (source_dir / "subdir" / "file2.txt").write_text("content2")

        dest_dir = tmp_path / "dest"

        # Act
        await install_directory(source_dir, dest_dir)

        # Assert
        assert (dest_dir / "file1.txt").read_text() == "content1"
        assert (dest_dir / "subdir" / "file2.txt").read_text() == "content2"

    @pytest.mark.asyncio
    async def test_install_file_skips_binary_files(self, tmp_path: Path) -> None:
        """Test that install_file skips binary files with warning."""
        # Arrange
        from mcp_guide.installer.core import install_file

        source = tmp_path / "binary.bin"
        source.write_bytes(b"\x00\x01\x02\xff\xfe")

        dest = tmp_path / "dest.bin"

        # Act
        result = await install_file(source, dest)

        # Assert
        assert result is False  # Skipped
        assert not dest.exists()

    @pytest.mark.asyncio
    async def test_install_file_preserves_permissions(self, tmp_path: Path) -> None:
        """Test that install_file preserves file permissions."""
        # Arrange
        from mcp_guide.installer.core import install_file

        source = tmp_path / "source.txt"
        source.write_text("content")
        source.chmod(0o755)

        dest = tmp_path / "dest.txt"

        # Act
        await install_file(source, dest)

        # Assert
        assert dest.stat().st_mode & 0o777 == 0o755


class TestInstallationOrchestration:
    """Tests for installation orchestration."""

    @pytest.mark.asyncio
    async def test_install_templates_performs_first_install(self, tmp_path: Path) -> None:
        """Test that install_templates performs first-time installation."""
        # Arrange
        from mcp_guide.installer.core import install_templates

        docroot = tmp_path / "docroot"
        archive_path = tmp_path / "originals.zip"

        # Act
        result = await install_templates(docroot, archive_path)

        # Assert
        assert docroot.exists()
        assert archive_path.exists()
        assert "files_installed" in result
        assert result["files_installed"] > 0

    @pytest.mark.asyncio
    async def test_update_templates_uses_smart_strategy(self, tmp_path: Path) -> None:
        """Test that update_templates uses smart update strategy."""
        # Arrange
        from mcp_guide.installer.core import update_templates

        docroot = tmp_path / "docroot"
        archive_path = tmp_path / "originals.zip"

        # Create existing installation
        docroot.mkdir()
        (docroot / "file.txt").write_text("User modified content\n")

        # Create archive with original
        from zipfile import ZipFile

        with ZipFile(archive_path, "w") as zf:
            zf.writestr("file.txt", "Original content\n")
            zf.writestr("README.md", "Archive readme\n")

        # Act
        result = await update_templates(docroot, archive_path)

        # Assert
        assert "files_processed" in result
        assert "skipped" in result or "patched" in result or "replaced" in result
