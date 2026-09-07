"""Host path expansion, deferred resolution and synchronous/asynchronous IO."""

from pathlib import Path

import pytest

from mcp_guide.lazy_path import LazyPath


def test_expansion_methods_keep_user_and_environment_expansion_distinct(monkeypatch):
    monkeypatch.setenv("GUIDE_LAZY_COMPONENT", "docs")
    lazy = LazyPath(Path("~/${GUIDE_LAZY_COMPONENT}"))
    assert str(lazy) == "~/${GUIDE_LAZY_COMPONENT}"
    assert repr(lazy) == "LazyPath('~/${GUIDE_LAZY_COMPONENT}')"
    assert lazy.expanduser() == str(Path.home() / "${GUIDE_LAZY_COMPONENT}")
    assert lazy.expandvars() == "~/docs"
    assert lazy.expand() == Path.home() / "docs"
    assert lazy.resolve() == (Path.home() / "docs").resolve()


@pytest.mark.parametrize("path,absolute", [("~/docs", True), ("$GUIDE_LAZY_ROOT/docs", True), ("docs/file", False)])
def test_absolute_classification_uses_expansion(monkeypatch, tmp_path, path, absolute):
    monkeypatch.setenv("GUIDE_LAZY_ROOT", str(tmp_path))
    assert LazyPath(path).is_absolute() is absolute


def test_resolution_is_deferred_then_cached(monkeypatch, tmp_path):
    monkeypatch.setenv("GUIDE_LAZY_ROOT", str(tmp_path / "initial"))
    lazy = LazyPath("$GUIDE_LAZY_ROOT/docs")
    monkeypatch.setenv("GUIDE_LAZY_ROOT", str(tmp_path / "before-resolution"))
    first = lazy.resolve()
    assert first == tmp_path / "before-resolution" / "docs"
    monkeypatch.setenv("GUIDE_LAZY_ROOT", str(tmp_path / "after-resolution"))
    assert lazy.resolve() is first
    assert str(lazy) == "$GUIDE_LAZY_ROOT/docs"


@pytest.mark.parametrize("expand", [True, False])
def test_strict_resolution_distinguishes_literal_and_expanded_paths(monkeypatch, tmp_path, expand):
    target = tmp_path / "actual"
    target.mkdir()
    monkeypatch.setenv("GUIDE_LAZY_COMPONENT", "actual")
    lazy = LazyPath(tmp_path / "$GUIDE_LAZY_COMPONENT")
    if expand:
        assert lazy.resolve(strict=True) == target
    else:
        with pytest.raises(FileNotFoundError):
            lazy.resolve(strict=True, expand=False)
    with pytest.raises(FileNotFoundError):
        LazyPath(tmp_path / "missing").resolve(strict=True, expand=expand)


@pytest.mark.anyio
async def test_aresolve_matches_resolve_and_supports_async_io(tmp_path, monkeypatch):
    target = tmp_path / "docs"
    target.mkdir()
    monkeypatch.setenv("GUIDE_LAZY_DOCS", str(target))
    lazy = LazyPath("$GUIDE_LAZY_DOCS")
    resolved = lazy.resolve()
    async_resolved = await LazyPath("$GUIDE_LAZY_DOCS").aresolve()
    assert Path(async_resolved) == resolved
    assert await async_resolved.exists()
    cached = await lazy.aresolve()
    assert Path(cached) == resolved
