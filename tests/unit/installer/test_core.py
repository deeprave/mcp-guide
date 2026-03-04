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

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("present.txt", True),
            ("missing.txt", False),
        ],
    )
    @pytest.mark.asyncio
    async def test_file_exists_in_archive(self, filename: str, expected: bool, tmp_path: Path) -> None:
        """Test file_exists_in_archive returns correct boolean."""
        archive_path = tmp_path / "archive.zip"
        with ZipFile(archive_path, "w") as zf:
            zf.writestr("present.txt", "content")
            zf.writestr("other.txt", "content")

        result = await file_exists_in_archive(archive_path, filename)
        assert result is expected


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

    @pytest.mark.parametrize(
        "target_content,diff_content,expected_success,expected_result",
        [
            (
                "Line 1\nLine 2\nLine 3\n",
                """--- /some/absolute/path/original.txt
+++ /another/absolute/path/modified.txt
@@ -1,3 +1,3 @@
 Line 1
-Line 2
+Line 2 modified
 Line 3
""",
                True,
                "Line 1\nLine 2 modified\nLine 3\n",
            ),
            (
                "Line 1\nDifferent content\nLine 3\n",
                """--- original.txt
+++ modified.txt
@@ -1,3 +1,3 @@
 Line 1
-Line 2
+Line 2 modified
 Line 3
""",
                False,
                None,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_apply_diff(
        self, target_content: str, diff_content: str, expected_success: bool, expected_result, tmp_path: Path
    ) -> None:
        """Test apply_diff with successful and failed patches."""
        target = tmp_path / "target.txt"
        target.write_text(target_content)

        success = await apply_diff(target, diff_content)

        assert success is expected_success
        if expected_result:
            assert target.read_text() == expected_result


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
        assert result == "skipped_binary"  # Returns status string
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
        assert "installed" in result
        assert result["installed"] > 0

    @pytest.mark.asyncio
    async def test_update_documents_uses_smart_strategy(self, tmp_path: Path) -> None:
        """Test that update_documents uses smart update strategy."""
        # Arrange
        from mcp_guide.installer.core import update_documents

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
        result = await update_documents(docroot, archive_path)

        # Assert
        assert "unchanged" in result or "patched" in result or "updated" in result or "installed" in result


class TestInstallFileSmartUpdate:
    """Tests for install_file smart update strategy."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scenario,should_raise",
        [
            ("same_path", True),
            ("different_path", False),
            ("nonexistent_path", False),
        ],
    )
    @pytest.mark.asyncio
    async def test_docroot_safety_check(self, scenario: str, should_raise: bool, tmp_path: Path) -> None:
        """Test docroot safety validation with various path scenarios."""
        from mcp_guide.installer.core import get_templates_path, validate_docroot_safety

        if scenario == "same_path":
            docroot = await get_templates_path()
        elif scenario == "different_path":
            docroot = tmp_path / "docroot"
            docroot.mkdir()
        else:  # nonexistent_path
            docroot = tmp_path / "nonexistent"

        if should_raise:
            with pytest.raises(ValueError, match="Docroot cannot be same as template source"):
                await validate_docroot_safety(docroot)
        else:
            await validate_docroot_safety(docroot)

    @pytest.mark.parametrize(
        "scenario,source_content,dest_content,archive_content,expected_status,check_backup",
        [
            ("skipped_binary", b"\x00\x01\x02\xff\xfe", None, None, "skipped_binary", False),
            ("installed", "content", None, None, "installed", False),
            ("unchanged", "same content", "same content", None, "unchanged", False),
            ("updated", "new content", "original content", "original content", "updated", False),
            (
                "patched",
                "line 1\nline 2 updated\nline 3\n",
                "line 1\nline 2\nline 3\nuser added line\n",
                "line 1\nline 2\nline 3\n",
                "patched",
                False,
            ),
            (
                "conflict",
                "completely different content\n",
                "line 1\nline 2\nuser changes that conflict\n",
                "original line 1\noriginal line 2\n",
                "conflict",
                True,
            ),
            ("no_archive_unchanged", "same content", "same content", False, "unchanged", False),
            ("no_archive_conflict", "new content", "old content", False, "conflict", True),
        ],
        ids=[
            "skipped_binary",
            "installed",
            "unchanged",
            "updated",
            "patched",
            "conflict",
            "no_archive_unchanged",
            "no_archive_conflict",
        ],
    )
    @pytest.mark.asyncio
    async def test_install_file_return_statuses(
        self, scenario, source_content, dest_content, archive_content, expected_status, check_backup, tmp_path: Path
    ) -> None:
        """Test install_file returns correct status for various scenarios."""
        from mcp_guide.installer.core import install_file

        # Setup source
        source = tmp_path / "source.txt"
        if isinstance(source_content, bytes):
            source.write_bytes(source_content)
        else:
            source.write_text(source_content)

        # Setup destination
        dest = tmp_path / "dest.txt"
        if dest_content:
            if isinstance(dest_content, bytes):
                dest.write_bytes(dest_content)
            else:
                dest.write_text(dest_content)

        # Setup archive
        archive_path = None
        if archive_content is not False and archive_content is not None:
            archive_path = tmp_path / "archive.zip"
            with ZipFile(archive_path, "w") as zf:
                zf.writestr("dest.txt", archive_content)

        # Act
        result = await install_file(source, dest, archive_path)

        # Assert
        assert result == expected_status

        if scenario == "skipped_binary":
            assert not dest.exists()
        elif scenario == "patched":
            content = dest.read_text()
            assert "line 2 updated" in content
            assert "user added line" in content

        if check_backup:
            backup = tmp_path / "orig.dest.txt"
            assert backup.exists()

    @pytest.mark.asyncio
    async def test_install_file_uses_archive_name_for_subdirectory_files(self, tmp_path: Path) -> None:
        """Test that install_file uses archive_name parameter for correct archive lookup."""
        # Arrange
        from mcp_guide.installer.core import install_file

        # Create source file
        source = tmp_path / "source" / "subdir" / "config.yaml"
        source.parent.mkdir(parents=True)
        source.write_text("version: 2\n")

        # Create dest file with user modifications
        dest = tmp_path / "dest" / "subdir" / "config.yaml"
        dest.parent.mkdir(parents=True)
        dest.write_text("version: 1\nuser_setting: custom\n")

        # Create archive with original using full relative path
        archive_path = tmp_path / "archive.zip"
        with ZipFile(archive_path, "w") as zf:
            zf.writestr("subdir/config.yaml", "version: 1\n")

        # Act - pass archive_name with full relative path
        result = await install_file(source, dest, archive_path, "subdir/config.yaml")

        # Assert
        assert result == "patched"
        content = dest.read_text()
        assert "version: 2" in content  # New version applied
        assert "user_setting: custom" in content  # User setting preserved

    @pytest.mark.asyncio
    async def test_install_file_handles_same_filename_in_different_directories(self, tmp_path: Path) -> None:
        """Test that files with same name in different directories are handled correctly."""
        # Arrange
        from mcp_guide.installer.core import create_archive, install_file

        # Create two files with same name in different dirs
        source_dir = tmp_path / "source"
        (source_dir / "dir1").mkdir(parents=True)
        (source_dir / "dir2").mkdir(parents=True)

        file1 = source_dir / "dir1" / "config.txt"
        file2 = source_dir / "dir2" / "config.txt"
        file1.write_text("content1\n")
        file2.write_text("content2\n")

        # Create archive
        archive = tmp_path / "archive.zip"
        await create_archive(archive, [file1, file2], source_dir)

        # Install both files
        dest_dir = tmp_path / "dest"
        dest1 = dest_dir / "dir1" / "config.txt"
        dest2 = dest_dir / "dir2" / "config.txt"

        await install_file(file1, dest1, archive, "dir1/config.txt")
        await install_file(file2, dest2, archive, "dir2/config.txt")

        # Modify only dest1
        dest1.write_text("content1\nuser changes\n")

        # Update with new versions
        file1.write_text("content1\nnew line\n")
        file2.write_text("content2\nnew line\n")

        # Act
        result1 = await install_file(file1, dest1, archive, "dir1/config.txt")
        result2 = await install_file(file2, dest2, archive, "dir2/config.txt")

        # Assert
        assert result1 == "patched"  # User modified, should patch
        assert result2 == "updated"  # Not modified, should update
        assert "user changes" in dest1.read_text()  # User changes preserved
        assert "new line" in dest1.read_text()  # New content applied
        assert "new line" in dest2.read_text()  # New content applied
