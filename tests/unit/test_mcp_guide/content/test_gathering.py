"""Tests for content gathering deduplication logic."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.content.gathering import gather_category_fileinfos, gather_content
from mcp_guide.content.utils import _gather_policy_partials, render_missing_policy
from mcp_guide.discovery.files import FileInfo
from mcp_guide.models import Category, Collection, Project
from mcp_guide.render.context import TemplateContext
from mcp_guide.result_constants import INSTRUCTION_MISSING_POLICY


def _make_file(name: str, *, source: str = "file") -> FileInfo:
    return FileInfo(
        path=Path(name),
        size=0,
        content_size=0,
        mtime=datetime(2024, 1, 1),
        name=name,
        source=source,
        content=f"content of {name}",
    )


class _MockSession:
    def __init__(self, docroot: str):
        self._docroot = docroot

    async def get_docroot(self):
        return self._docroot


@pytest.mark.anyio
async def test_stored_and_filesystem_same_name_both_appear(tmp_path, monkeypatch):
    """Stored document and filesystem file with same name must both appear."""
    category_dir = tmp_path / "docs"
    category_dir.mkdir()
    (category_dir / "readme.md").write_text("filesystem content")

    project = Project(
        name="test",
        categories={"docs": Category(dir="docs", name="docs", patterns=["*.md"])},
    )

    stored_file = _make_file("readme.md", source="store")
    stored_file.category = project.categories["docs"]

    original_gather = gather_content.__wrapped__ if hasattr(gather_content, "__wrapped__") else None

    # Patch discover_documents to return both filesystem and stored
    async def mock_discover(category_dir, patterns, category=None):
        fs_file = _make_file("readme.md", source="file")
        return [fs_file, stored_file]

    monkeypatch.setattr("mcp_guide.content.gathering.discover_documents", mock_discover)

    session = _MockSession(str(tmp_path))
    result = await gather_content(session, project, "docs")

    assert len(result) == 2
    sources = {f.source for f in result}
    assert sources == {"file", "store"}


@pytest.mark.anyio
async def test_stored_doc_deduped_across_overlapping_collections(tmp_path, monkeypatch):
    """Same stored document appearing via two collections must be deduped."""
    category_dir = tmp_path / "docs"
    category_dir.mkdir()

    project = Project(
        name="test",
        categories={"docs": Category(dir="docs", name="docs", patterns=["*.md"])},
        collections={
            "col1": Collection(categories=["docs"]),
            "col2": Collection(categories=["docs"]),
        },
    )

    async def mock_discover(category_dir, patterns, category=None):
        stored = _make_file("notes.md", source="store")
        stored.category = project.categories["docs"]
        return [stored]

    monkeypatch.setattr("mcp_guide.content.gathering.discover_documents", mock_discover)

    session = _MockSession(str(tmp_path))
    result = await gather_content(session, project, "col1,col2")

    # Same (category, name) from two collections → only one copy
    stored_results = [f for f in result if f.source == "store"]
    assert len(stored_results) == 1


# --- Tests for _ prefix exclusion in gather_category_fileinfos ---


@pytest.mark.anyio
async def test_underscore_prefix_file_excluded(tmp_path):
    """Filesystem files with _ prefix are excluded from category discovery."""
    category_dir = tmp_path / "policies"
    category_dir.mkdir()
    (category_dir / "_INDEX.md").write_text("# Index")
    (category_dir / "conservative.md").write_text("# Conservative")

    project = Project(
        name="test",
        categories={"policies": Category(dir="policies", name="policies", patterns=["*.md"])},
    )
    session = _MockSession(str(tmp_path))
    result = await gather_category_fileinfos(session, project, "policies")

    assert len(result) == 1
    assert result[0].name == "conservative.md"


@pytest.mark.anyio
async def test_underscore_prefix_directory_excluded(tmp_path):
    """Files inside _ prefixed subdirectories are excluded from category discovery."""
    category_dir = tmp_path / "policies"
    (category_dir / "_system").mkdir(parents=True)
    (category_dir / "_system" / "missing_policy.md").write_text("# Missing")
    (category_dir / "conservative.md").write_text("# Conservative")

    project = Project(
        name="test",
        categories={"policies": Category(dir="policies", name="policies", patterns=["**/*.md"])},
    )
    session = _MockSession(str(tmp_path))
    result = await gather_category_fileinfos(session, project, "policies")

    assert len(result) == 1
    assert result[0].name == "conservative.md"


@pytest.mark.anyio
async def test_underscore_prefix_in_subdirectory_excluded(tmp_path):
    """_ prefixed files in nested subdirectories are excluded."""
    category_dir = tmp_path / "policies"
    subdir = category_dir / "git" / "ops"
    subdir.mkdir(parents=True)
    (subdir / "_notes.md").write_text("# Notes")
    (subdir / "conservative.md").write_text("# Conservative")

    project = Project(
        name="test",
        categories={"policies": Category(dir="policies", name="policies", patterns=["**/*.md"])},
    )
    session = _MockSession(str(tmp_path))
    result = await gather_category_fileinfos(session, project, "policies")

    assert len(result) == 1
    assert result[0].name == "git/ops/conservative.md"


@pytest.mark.anyio
async def test_stored_document_with_underscore_not_excluded(tmp_path):
    """Stored documents with _ prefix are NOT excluded — they are user-imported."""
    category_dir = tmp_path / "policies"
    category_dir.mkdir()

    project = Project(
        name="test",
        categories={"policies": Category(dir="policies", name="policies", patterns=["*.md"])},
    )

    async def mock_discover(base_dir, patterns, category=None):
        stored = FileInfo(
            path=Path("_custom.md"),
            size=0,
            content_size=0,
            mtime=datetime(2024, 1, 1),
            name="_custom.md",
            source="store",
        )
        return [stored]

    session = _MockSession(str(tmp_path))
    from unittest.mock import patch

    with patch("mcp_guide.content.gathering.discover_documents", side_effect=mock_discover):
        result = await gather_category_fileinfos(session, project, "policies")

    assert len(result) == 1
    assert result[0].name == "_custom.md"


# --- Tests for sub-path filtering via trailing slash ---


@pytest.mark.anyio
async def test_trailing_slash_filters_to_matching_configured_patterns(tmp_path):
    """Trailing slash in pattern filters configured patterns to those starting with the prefix."""
    category_dir = tmp_path / "policies"
    subdir = category_dir / "git" / "ops"
    subdir.mkdir(parents=True)
    (category_dir / "git" / "ops" / "conservative.md").write_text("# Conservative")
    (category_dir / "git" / "ops" / "agent-assisted.md").write_text("# Agent")
    (category_dir / "testing" / "strict.md").write_text("# Strict") if (category_dir / "testing").mkdir(
        parents=True
    ) or True else None

    project = Project(
        name="test",
        categories={
            "policies": Category(
                dir="policies",
                name="policies",
                patterns=["git/ops/conservative*", "testing/strict*"],
            )
        },
    )
    session = _MockSession(str(tmp_path))
    # trailing slash pattern → sub-path filter for "git/ops/"
    result = await gather_category_fileinfos(session, project, "policies", patterns=["git/ops/"])

    assert len(result) == 1
    assert result[0].name == "git/ops/conservative.md"


@pytest.mark.anyio
async def test_trailing_slash_no_matching_configured_patterns_returns_empty(tmp_path):
    """When no configured patterns start with the sub-path prefix, result is empty."""
    category_dir = tmp_path / "policies"
    (category_dir / "testing").mkdir(parents=True)
    (category_dir / "testing" / "strict.md").write_text("# Strict")

    project = Project(
        name="test",
        categories={
            "policies": Category(
                dir="policies",
                name="policies",
                patterns=["testing/strict*"],
            )
        },
    )
    session = _MockSession(str(tmp_path))
    result = await gather_category_fileinfos(session, project, "policies", patterns=["git/ops/"])

    assert result == []


@pytest.mark.anyio
async def test_no_trailing_slash_uses_pattern_as_override(tmp_path):
    """Without trailing slash, passed pattern overrides configured patterns (existing behaviour)."""
    category_dir = tmp_path / "policies"
    subdir = category_dir / "git" / "ops"
    subdir.mkdir(parents=True)
    (subdir / "conservative.md").write_text("# Conservative")
    (category_dir / "testing").mkdir(parents=True)
    (category_dir / "testing" / "strict.md").write_text("# Strict")

    project = Project(
        name="test",
        categories={
            "policies": Category(
                dir="policies",
                name="policies",
                patterns=["testing/strict*"],
            )
        },
    )
    session = _MockSession(str(tmp_path))
    # No trailing slash → override: use "git/ops/conservative*" as pattern
    result = await gather_category_fileinfos(session, project, "policies", patterns=["git/ops/conservative*"])

    assert len(result) == 1
    assert result[0].name == "git/ops/conservative.md"


@pytest.mark.anyio
async def test_trailing_slash_multiple_matching_patterns(tmp_path):
    """Multiple configured patterns under the sub-path prefix are all used."""
    category_dir = tmp_path / "policies"
    subdir = category_dir / "git" / "ops"
    subdir.mkdir(parents=True)
    (subdir / "conservative.md").write_text("# Conservative")
    (subdir / "agent-assisted.md").write_text("# Agent")

    project = Project(
        name="test",
        categories={
            "policies": Category(
                dir="policies",
                name="policies",
                patterns=["git/ops/conservative*", "git/ops/agent-assisted*"],
            )
        },
    )
    session = _MockSession(str(tmp_path))
    result = await gather_category_fileinfos(session, project, "policies", patterns=["git/ops/"])

    assert len(result) == 2
    names = {r.name for r in result}
    assert names == {"git/ops/conservative.md", "git/ops/agent-assisted.md"}


# --- Tests for render_missing_policy ---


def test_render_missing_policy_contains_constant():
    """Placeholder must contain INSTRUCTION_MISSING_POLICY."""
    result = render_missing_policy("git/ops")
    assert INSTRUCTION_MISSING_POLICY in result


def test_render_missing_policy_contains_topic():
    """Placeholder must contain the topic name."""
    result = render_missing_policy("testing")
    assert "testing" in result


def test_render_missing_policy_different_topics():
    """Each topic produces distinct output."""
    a = render_missing_policy("git/ops")
    b = render_missing_policy("testing")
    assert a != b


# --- Tests for _gather_policy_partials ---


def _make_template_context(session=None, project=None) -> TemplateContext:
    ctx = TemplateContext({})
    if session is not None:
        ctx.session = session
    if project is not None:
        ctx.project = project
    return ctx


@pytest.mark.anyio
async def test_gather_policy_partials_no_policies_key_returns_empty(tmp_path):
    """Template without 'policies:' frontmatter returns empty dict."""
    policy_file = tmp_path / "doc.md.mustache"
    policy_file.write_text("---\ntype: agent/instruction\n---\nNo policies here.")

    file_info = FileInfo(
        path=policy_file,
        size=policy_file.stat().st_size,
        content_size=0,
        mtime=datetime(2024, 1, 1),
        name="doc.md",
    )
    ctx = _make_template_context()
    result = await _gather_policy_partials(file_info, ctx, tmp_path, {})
    assert result == {}


@pytest.mark.anyio
async def test_gather_policy_partials_no_session_returns_empty(tmp_path):
    """Without session in context, returns empty dict."""
    policy_file = tmp_path / "doc.md.mustache"
    policy_file.write_text("---\npolicies:\n  - git/ops\n---\nContent.")

    file_info = FileInfo(
        path=policy_file,
        size=policy_file.stat().st_size,
        content_size=0,
        mtime=datetime(2024, 1, 1),
        name="doc.md",
    )
    ctx = _make_template_context()  # no session
    result = await _gather_policy_partials(file_info, ctx, tmp_path, {})
    assert result == {}


@pytest.mark.anyio
async def test_gather_policy_partials_no_match_returns_placeholder(tmp_path):
    """Topic with no matching policy files → placeholder content for that topic."""
    policy_file = tmp_path / "doc.md.mustache"
    policy_file.write_text("---\npolicies:\n  - git/ops\n---\nContent.")

    file_info = FileInfo(
        path=policy_file,
        size=policy_file.stat().st_size,
        content_size=0,
        mtime=datetime(2024, 1, 1),
        name="doc.md",
    )

    project = Project(
        name="test",
        categories={"policies": Category(dir="policies", name="policies", patterns=["testing/strict*"])},
    )
    session = _MockSession(str(tmp_path))
    (tmp_path / "policies" / "testing").mkdir(parents=True)
    (tmp_path / "policies" / "testing" / "strict.md").write_text("# Strict")

    ctx = _make_template_context(session=session, project=project)
    result = await _gather_policy_partials(file_info, ctx, tmp_path, {})

    assert "git/ops" in result
    assert INSTRUCTION_MISSING_POLICY in result["git/ops"]
    assert "git/ops" in result["git/ops"]


@pytest.mark.anyio
async def test_gather_policy_partials_matching_topic_renders_content(tmp_path):
    """Topic with a matching policy file → rendered content returned."""
    # Template that declares a policy dependency
    doc_file = tmp_path / "doc.md.mustache"
    doc_file.write_text("---\npolicies:\n  - git/ops\n---\nContent.")

    file_info = FileInfo(
        path=doc_file,
        size=doc_file.stat().st_size,
        content_size=0,
        mtime=datetime(2024, 1, 1),
        name="doc.md",
    )

    # Create policies category with a matching document
    policies_dir = tmp_path / "policies"
    (policies_dir / "git" / "ops").mkdir(parents=True)
    (policies_dir / "git" / "ops" / "conservative.md").write_text(
        "---\ntype: agent/instruction\n---\nUse conservative git ops."
    )

    project = Project(
        name="test",
        categories={
            "policies": Category(
                dir="policies",
                name="policies",
                patterns=["git/ops/conservative*"],
            )
        },
    )
    session = _MockSession(str(tmp_path))
    ctx = _make_template_context(session=session, project=project)

    result = await _gather_policy_partials(file_info, ctx, tmp_path, {})

    assert "git/ops" in result
    assert "Use conservative git ops." in result["git/ops"]
