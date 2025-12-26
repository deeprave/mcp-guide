"""Tests for LazyPath."""

import os
from pathlib import Path

import pytest

from mcp_guide.lazy_path import LazyPath


async def test_lazypath_with_tilde():
    """Test LazyPath with tilde path."""
    lazy = LazyPath("~/test/path")
    assert str(lazy) == "~/test/path"
    assert "~" not in lazy.expanduser()
    assert lazy.expanduser().startswith(str(Path.home()))


async def test_lazypath_with_environment_variable():
    """Test LazyPath with environment variable."""
    os.environ["TEST_VAR"] = "/test/value"
    lazy = LazyPath("${TEST_VAR}/path")
    assert str(lazy) == "${TEST_VAR}/path"
    assert lazy.expandvars() == "/test/value/path"


async def test_lazypath_resolve_expands_both():
    """Test LazyPath.resolve() expands both tilde and env vars."""
    os.environ["TEST_VAR"] = "subdir"
    lazy = LazyPath("~/${TEST_VAR}/file.txt")
    resolved = lazy.resolve()
    assert "~" not in str(resolved)
    assert "${TEST_VAR}" not in str(resolved)
    assert str(Path.home()) in str(resolved)
    assert "subdir" in str(resolved)


async def test_lazypath_is_absolute_after_expansion():
    """Test LazyPath.is_absolute() checks after expansion."""
    lazy_tilde = LazyPath("~/test")
    assert lazy_tilde.is_absolute()

    os.environ["TEST_VAR"] = str(Path.home())
    lazy_var = LazyPath("${TEST_VAR}/test")
    assert lazy_var.is_absolute()

    lazy_relative = LazyPath("relative/path")
    assert not lazy_relative.is_absolute()


async def test_lazypath_lazy_evaluation():
    """Test LazyPath doesn't resolve until .resolve() is called."""
    lazy = LazyPath("~/test")
    assert lazy._resolved_path is None
    lazy.resolve()
    assert lazy._resolved_path is not None


async def test_lazypath_caches_resolved_path():
    """Test LazyPath caches resolved path after first resolution."""
    lazy = LazyPath("~/test")
    first = lazy.resolve()
    second = lazy.resolve()
    assert first is second


async def test_lazypath_str_returns_original():
    """Test __str__ returns original path string."""
    original = "~/test/${VAR}/path"
    lazy = LazyPath(original)
    assert str(lazy) == original


async def test_lazypath_repr():
    """Test __repr__ format."""
    lazy = LazyPath("~/test")
    assert repr(lazy) == "LazyPath('~/test')"


async def test_lazypath_from_path_object():
    """Test LazyPath can be created from Path object."""
    path = Path("~/test")
    lazy = LazyPath(path)
    assert str(lazy) == "~/test"


async def test_lazypath_resolve_no_expand():
    """Test LazyPath.resolve(expand=False) doesn't expand variables."""
    os.environ["TEST_VAR"] = "value"
    lazy = LazyPath("${TEST_VAR}/path")

    # With expand=False, should try to resolve literal path
    # This will fail if path doesn't exist, but we can check the behavior
    with pytest.raises(OSError):
        lazy.resolve(expand=False, strict=True)


async def test_lazypath_resolve_strict():
    """Test LazyPath.resolve(strict=True) raises if path doesn't exist."""
    lazy = LazyPath("~/nonexistent_path_12345")
    with pytest.raises(FileNotFoundError):
        lazy.resolve(strict=True)


async def test_lazypath_expanduser_only():
    """Test expanduser() only expands tilde, not env vars."""
    os.environ["TEST_VAR"] = "value"
    lazy = LazyPath("~/${TEST_VAR}")
    expanded = lazy.expanduser()
    assert "~" not in expanded
    assert "${TEST_VAR}" in expanded


async def test_lazypath_expandvars_only():
    """Test expandvars() only expands env vars, not tilde."""
    os.environ["TEST_VAR"] = "value"
    lazy = LazyPath("~/${TEST_VAR}")
    expanded = lazy.expandvars()
    assert "~" in expanded
    assert "${TEST_VAR}" not in expanded
    assert "value" in expanded
