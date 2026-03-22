"""Tests for category_list_files source filter parameter."""

import pytest
from pydantic import ValidationError

from mcp_guide.tools.tool_category import CategoryListFilesArgs


def test_source_filter_accepts_files():
    """Source filter accepts 'files'."""
    args = CategoryListFilesArgs(category="docs", source="files")
    assert args.source == "files"


def test_source_filter_accepts_stored():
    """Source filter accepts 'stored'."""
    args = CategoryListFilesArgs(category="docs", source="stored")
    assert args.source == "stored"


def test_source_filter_defaults_to_none():
    """Source filter defaults to None (both sources)."""
    args = CategoryListFilesArgs(category="docs")
    assert args.source is None


def test_source_filter_rejects_invalid_value():
    """Source filter rejects invalid values."""
    with pytest.raises(ValidationError):
        CategoryListFilesArgs(category="docs", source="invalid")
