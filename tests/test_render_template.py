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


@pytest.mark.asyncio
async def test_render_template_requires_list_scalar_match():
    """Test list requirement with scalar value - should match if in list."""
    test_file = Path("tests/fixtures/test_requires_list_scalar.mustache")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("---\nrequires-phase: [discussion, planning]\n---\nContent")

    try:
        file_info = FileInfo(
            path=test_file,
            size=test_file.stat().st_size,
            content_size=7,
            mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
            name=test_file.name,
        )

        # Should match - discussion is in list
        result = await render_template(
            file_info=file_info,
            base_dir=test_file.parent,
            project_flags={"phase": "discussion"},
        )
        assert result is not None

        # Should not match - implementation not in list
        result = await render_template(
            file_info=file_info,
            base_dir=test_file.parent,
            project_flags={"phase": "implementation"},
        )
        assert result is None
    finally:
        test_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_render_template_requires_list_with_list_any_match():
    """Test list requirement with list value - should match if ANY required in actual."""
    test_file = Path("tests/fixtures/test_requires_list_list.mustache")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("---\nrequires-workflow: [discussion, implementation]\n---\nContent")

    try:
        file_info = FileInfo(
            path=test_file,
            size=test_file.stat().st_size,
            content_size=7,
            mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
            name=test_file.name,
        )

        # Should match - discussion is present
        result = await render_template(
            file_info=file_info,
            base_dir=test_file.parent,
            project_flags={"workflow": ["discussion", "planning", "check"]},
        )
        assert result is not None

        # Should not match - neither discussion nor implementation present
        result = await render_template(
            file_info=file_info,
            base_dir=test_file.parent,
            project_flags={"workflow": ["planning", "check", "review"]},
        )
        assert result is None
    finally:
        test_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_render_template_requires_list_with_dict_any_key():
    """Test list requirement with dict value - should match if ANY required key exists."""
    test_file = Path("tests/fixtures/test_requires_list_dict.mustache")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("---\nrequires-config: [feature1, feature2]\n---\nContent")

    try:
        file_info = FileInfo(
            path=test_file,
            size=test_file.stat().st_size,
            content_size=7,
            mtime=datetime.fromtimestamp(test_file.stat().st_mtime),
            name=test_file.name,
        )

        # Should match - feature1 key exists
        result = await render_template(
            file_info=file_info,
            base_dir=test_file.parent,
            project_flags={"config": {"feature1": True, "feature3": False}},
        )
        assert result is not None

        # Should not match - neither feature1 nor feature2 keys exist
        result = await render_template(
            file_info=file_info,
            base_dir=test_file.parent,
            project_flags={"config": {"feature3": True, "feature4": False}},
        )
        assert result is None
    finally:
        test_file.unlink(missing_ok=True)
