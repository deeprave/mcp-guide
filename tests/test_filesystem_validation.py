"""Test validation of required parameters in filesystem tools."""

import pytest

from mcp_guide.filesystem.tools import send_command_location, send_directory_listing, send_file_content


@pytest.mark.asyncio
async def test_send_file_content_missing_path():
    """Test send_file_content with missing path."""
    result = await send_file_content(context=None, path="", content="test content")
    assert not result.success
    assert result.error_type == "validation_error"
    assert result.error_data is not None
    assert "path" in result.error_data


@pytest.mark.asyncio
async def test_send_file_content_missing_content():
    """Test send_file_content with missing content."""
    result = await send_file_content(context=None, path="/test/file.txt", content="")
    assert not result.success
    assert result.error_type == "validation_error"
    assert result.error_data is not None
    assert "content" in result.error_data


@pytest.mark.asyncio
async def test_send_file_content_missing_both():
    """Test send_file_content with both path and content missing."""
    result = await send_file_content(context=None, path="", content="")
    assert not result.success
    assert result.error_type == "validation_error"
    assert result.error_data is not None
    assert "path" in result.error_data
    assert "content" in result.error_data
    assert len(result.error_data) == 2


@pytest.mark.asyncio
async def test_send_directory_listing_missing_path():
    """Test send_directory_listing with missing path."""
    result = await send_directory_listing(context=None, path="", files=[])
    assert not result.success
    assert result.error_type == "validation_error"
    assert result.error_data is not None
    assert "path" in result.error_data


@pytest.mark.asyncio
async def test_send_directory_listing_missing_entries():
    """Test send_directory_listing with None entries."""
    result = await send_directory_listing(context=None, path="/test", files=None)  # type: ignore[arg-type]
    assert not result.success
    assert result.error_type == "validation_error"
    assert result.error_data is not None
    assert "entries" in result.error_data


@pytest.mark.asyncio
async def test_send_command_location_missing_command():
    """Test send_command_location with missing command."""
    result = await send_command_location(context=None, command="")
    assert not result.success
    assert result.error_type == "validation_error"
    assert result.error_data is not None
    assert "command" in result.error_data
