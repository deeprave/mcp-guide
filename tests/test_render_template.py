"""Tests for render.template module."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.template import render_template


@pytest.mark.asyncio
async def test_render_template_simple():
    """Test render_template with a simple template file."""
    # Create a test template file
    test_file = Path("tests/fixtures/test_template.mustache")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("---\ntype: agent/instruction\n---\nHello {{name}}!")

    try:
        file_info = FileInfo(
            path=test_file,
            size=test_file.stat().st_size,
            content_size=12,  # "Hello {{name}}!"
            mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
            name=test_file.name,
        )

        result = await render_template(
            file_info=file_info,
            base_dir=test_file.parent,
            project_flags={},
        )

        assert result is not None
        assert result.template_path == test_file
        assert result.template_name == test_file.name
        assert result.frontmatter["type"] == "agent/instruction"
    finally:
        test_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_render_template_requires_flag_present():
    """Test render_template returns content when required flag is present."""
    test_file = Path("tests/fixtures/test_requires.mustache")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("---\nrequires-feature: true\n---\nContent")

    try:
        file_info = FileInfo(
            path=test_file,
            size=test_file.stat().st_size,
            content_size=7,
            mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
            name=test_file.name,
        )

        result = await render_template(
            file_info=file_info,
            base_dir=test_file.parent,
            project_flags={"feature": True},
        )

        assert result is not None
    finally:
        test_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_render_template_requires_flag_missing():
    """Test render_template returns None when required flag is missing."""
    test_file = Path("tests/fixtures/test_requires_missing.mustache")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("---\nrequires-feature: true\n---\nContent")

    try:
        file_info = FileInfo(
            path=test_file,
            size=test_file.stat().st_size,
            content_size=7,
            mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
            name=test_file.name,
        )

        result = await render_template(
            file_info=file_info,
            base_dir=test_file.parent,
            project_flags={},
        )

        assert result is None
    finally:
        test_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_render_template_requires_flag_falsy():
    """Test render_template returns None when required flag is falsy."""
    test_file = Path("tests/fixtures/test_requires_falsy.mustache")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("---\nrequires-feature: true\n---\nContent")

    try:
        file_info = FileInfo(
            path=test_file,
            size=test_file.stat().st_size,
            content_size=7,
            mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
            name=test_file.name,
        )

        result = await render_template(
            file_info=file_info,
            base_dir=test_file.parent,
            project_flags={"feature": False},
        )

        assert result is None
    finally:
        test_file.unlink(missing_ok=True)
