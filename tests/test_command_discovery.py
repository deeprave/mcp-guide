"""Tests for command discovery functionality."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from mcp_guide.discovery.files import FileInfo


class TestCommandDiscovery:
    """Test command discovery in _commands directory."""

    @pytest.mark.anyio
    async def test_discover_commands_basic(self) -> None:
        """Should discover basic commands in _commands directory."""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            commands_dir = Path(temp_dir) / "_commands"
            commands_dir.mkdir()

            # Create test command files
            (commands_dir / "help.md").write_text("# Help Command\nShows available commands.")
            (commands_dir / "status.mustache").write_text("# Status\nSystem status information.")

            # Mock discover_documents to return our test files
            mock_files = [
                FileInfo(
                    path=Path("help.md"),  # Relative path
                    size=100,
                    content_size=100,
                    mtime=1234567890,
                    name="help.md",
                    content="",
                    ctime=1234567890,
                ),
                FileInfo(
                    path=Path("status.mustache"),  # Relative path
                    size=150,
                    content_size=150,
                    mtime=1234567890,
                    name="status.mustache",
                    content="",
                    ctime=1234567890,
                ),
            ]

            with patch("mcp_guide.discovery.commands.discover_documents", new=AsyncMock(return_value=mock_files)):
                # Import and test the function (to be implemented)
                from mcp_guide.discovery.commands import discover_commands

                commands = await discover_commands(commands_dir)

                assert len(commands) == 2
                assert any(cmd["name"] == "help" for cmd in commands)
                assert any(cmd["name"] == "status" for cmd in commands)

    @pytest.mark.anyio
    async def test_discover_subcommands(self) -> None:
        """Should discover subcommands in nested directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            commands_dir = Path(temp_dir) / "_commands"
            create_dir = commands_dir / "create"
            create_dir.mkdir(parents=True)

            # Create nested command files
            (create_dir / "category.md").write_text("# Create Category\nCreates a new category.")
            (create_dir / "collection.mustache").write_text("# Create Collection\nCreates a new collection.")

            mock_files = [
                FileInfo(
                    path=Path("create/category.md"),  # Relative path
                    size=100,
                    content_size=100,
                    mtime=1234567890,
                    name="create/category.md",
                    content="",
                    ctime=1234567890,
                ),
                FileInfo(
                    path=Path("create/collection.mustache"),  # Relative path
                    size=150,
                    content_size=150,
                    mtime=1234567890,
                    name="create/collection.mustache",
                    content="",
                    ctime=1234567890,
                ),
            ]

            with patch("mcp_guide.discovery.commands.discover_documents", new=AsyncMock(return_value=mock_files)):
                from mcp_guide.discovery.commands import discover_commands

                commands = await discover_commands(commands_dir)

                assert len(commands) == 2
                assert any(cmd["name"] == "create/category" for cmd in commands)
                assert any(cmd["name"] == "create/collection" for cmd in commands)

    @pytest.mark.anyio
    async def test_discover_commands_with_front_matter(self) -> None:
        """Should extract metadata from front matter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            commands_dir = Path(temp_dir) / "_commands"
            commands_dir.mkdir()

            # Create command with front matter
            help_content = """---
description: Shows available commands and usage information
usage: ":help [command]"
examples:
  - ":help"
  - ":help create/category"
---
# Help Command

This command shows all available commands.
"""
            (commands_dir / "help.md").write_text(help_content)

            mock_files = [
                FileInfo(
                    path=Path("help.md"),  # Relative path
                    size=len(help_content),
                    content_size=len(help_content),
                    mtime=1234567890,
                    name="help.md",
                    content=help_content,
                    ctime=1234567890,
                )
            ]

            with patch("mcp_guide.discovery.commands.discover_documents", new=AsyncMock(return_value=mock_files)):
                from mcp_guide.discovery.commands import discover_commands

                commands = await discover_commands(commands_dir)

                assert len(commands) == 1
                cmd = commands[0]
                assert cmd["name"] == "help"
                assert cmd["description"] == "Shows available commands and usage information"
                assert cmd["usage"] == ":help [command]"
                assert len(cmd["examples"]) == 2

    @pytest.mark.anyio
    async def test_discover_commands_without_front_matter(self) -> None:
        """Should handle commands without front matter gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            commands_dir = Path(temp_dir) / "_commands"
            commands_dir.mkdir()

            # Create command without front matter
            (commands_dir / "simple.md").write_text("# Simple Command\nJust a simple command.")

            mock_files = [
                FileInfo(
                    path=Path("simple.md"),  # Relative path
                    size=100,
                    content_size=100,
                    mtime=1234567890,
                    name="simple.md",
                    content="# Simple Command\nJust a simple command.",
                    ctime=1234567890,
                )
            ]

            with patch("mcp_guide.discovery.commands.discover_documents", new=AsyncMock(return_value=mock_files)):
                from mcp_guide.discovery.commands import discover_commands

                commands = await discover_commands(commands_dir)

                assert len(commands) == 1
                cmd = commands[0]
                assert cmd["name"] == "simple"
                assert cmd["description"] == ""  # Should default to empty
                assert cmd["usage"] == ""
                assert cmd["examples"] == []

    @pytest.mark.anyio
    async def test_discover_commands_filters_by_requirements(self) -> None:
        """Should filter commands based on requires-* frontmatter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            commands_dir = Path(temp_dir) / "_commands"
            commands_dir.mkdir()

            # Command with unmet requirement
            filtered_content = """---
requires-feature: enabled
description: Feature command
---
# Feature Command
"""
            (commands_dir / "feature.md").write_text(filtered_content)

            # Command with met requirement
            included_content = """---
requires-workflow: true
description: Workflow command
---
# Workflow Command
"""
            (commands_dir / "workflow.md").write_text(included_content)

            mock_files = [
                FileInfo(
                    path=Path("feature.md"),
                    size=100,
                    content_size=100,
                    mtime=1234567890,
                    name="feature.md",
                    content=filtered_content,
                    ctime=1234567890,
                ),
                FileInfo(
                    path=Path("workflow.md"),
                    size=100,
                    content_size=100,
                    mtime=1234567890,
                    name="workflow.md",
                    content=included_content,
                    ctime=1234567890,
                ),
            ]

            # Mock context with workflow=true but feature=false
            mock_context = {"workflow": True, "feature": False}

            with (
                patch("mcp_guide.discovery.commands.discover_documents", new=AsyncMock(return_value=mock_files)),
                patch("mcp_guide.render.cache.get_template_contexts", new=AsyncMock(return_value=mock_context)),
            ):
                from mcp_guide.discovery.commands import discover_commands

                commands = await discover_commands(commands_dir)

                # Should only include workflow command
                assert len(commands) == 1
                assert commands[0]["name"] == "workflow"


class TestCommandDiscoveryCaching:
    """Test command discovery caching with guide-development flag."""

    @pytest.mark.anyio
    async def test_cache_behavior_documented(self) -> None:
        """Document cache behavior: results are cached in the session's command_cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            commands_dir = Path(temp_dir) / "_commands"
            commands_dir.mkdir()
            (commands_dir / "test.md").write_text("# Test")

            from unittest.mock import Mock

            from mcp_guide.discovery.commands import discover_commands

            mock_session = Mock()
            mock_session.command_cache = {}

            with patch("mcp_guide.session.get_active_session", return_value=mock_session):
                result1 = await discover_commands(commands_dir)
                assert len(result1) > 0
                assert len(mock_session.command_cache) > 0
