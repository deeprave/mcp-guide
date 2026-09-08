"""Tests for content gathering deduplication logic."""

from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest
import yaml
from tests.helpers import create_bound_test_session, request_context_for

from mcp_guide.content.gathering import gather_category_fileinfos, gather_content
from mcp_guide.content.utils import _gather_policy_partials, render_missing_policy
from mcp_guide.discovery.files import FileInfo
from mcp_guide.models import Category, Collection, Project
from mcp_guide.models.exceptions import NoProjectError
from mcp_guide.render.cache_policy import CachePolicy
from mcp_guide.render.context import TemplateContext
from mcp_guide.result_constants import INSTRUCTION_MISSING_POLICY
from mcp_guide.runtime import RequestContext
from mcp_guide.store.document_store import add_document


class _MockSession:
    def __init__(self, docroot: str, project=None):
        self._docroot = docroot
        self._project = project

    @property
    def runtime(self):
        return self

    async def get_docroot(self):
        return self._docroot

    def resolve_document_path(self, relative_path):
        return Path(self._docroot) / relative_path

    async def get_project(self):
        if self._project is None:
            raise NoProjectError("no project")
        return self._project


async def _request_context(tmp_path, session=None):
    """Build a RequestContext whose document resolver is rooted at ``tmp_path``."""
    resolved = session if session is not None else _MockSession(str(tmp_path))
    return RequestContext(
        session_id="gather",
        session=resolved,
        seq=1,
        document_path_resolver=lambda relative: Path(tmp_path) / relative,
    )


@pytest.mark.anyio
async def test_discovery_keeps_both_sources_and_deduplicates_collections(tmp_path, monkeypatch):
    """Same-named sources remain distinct; overlapping collections do not duplicate either."""
    category_dir = tmp_path / "docs"
    category_dir.mkdir()
    (category_dir / "readme.md").write_text("Filesystem content")
    monkeypatch.setattr("mcp_guide.store.document_store.get_documents_db", lambda: tmp_path / "documents.db")
    await add_document("docs", "readme.md", "/client/readme.md", "file", "Stored content")
    project = Project(
        name="test",
        categories={"docs": Category(dir="docs", name="docs", patterns=["*.md"])},
        collections={"col1": Collection(categories=["docs"]), "col2": Collection(categories=["docs"])},
    )
    context = await _request_context(tmp_path)
    for expression in ("docs", "col1,col2"):
        result = await gather_content(context, project, expression)
        assert {(file.name, file.source) for file in result} == {("readme.md", "file"), ("readme.md", "store")}
        assert len(result) == 2
        for file in result:
            file.resolve(context.resolve_document_path, "docs")
        assert {await file.read_raw() for file in result} == {"Filesystem content", "Stored content"}


@pytest.mark.anyio
async def test_underscore_components_exclude_files_but_not_stored_documents(tmp_path, monkeypatch):
    """Filter every filesystem path component without filtering user-stored document names."""
    category_dir = tmp_path / "policies"
    for name in ("_INDEX.md", "_system/hidden.md", "git/ops/_notes.md", "git/ops/visible.md"):
        path = category_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
    monkeypatch.setattr("mcp_guide.store.document_store.get_documents_db", lambda: tmp_path / "documents.db")
    await add_document("policies", "_custom.md", "/client/custom.md", "file", "Stored policy")
    project = Project(
        name="test",
        categories={"policies": Category(dir="policies", name="policies", patterns=["**/*.md"])},
    )
    result = await gather_category_fileinfos(await _request_context(tmp_path), project, "policies")
    assert {(file.name, file.source) for file in result} == {("git/ops/visible.md", "file"), ("_custom.md", "store")}


# --- Tests for sub-path filtering via trailing slash ---


@pytest.mark.anyio
async def test_trailing_slash_filters_to_matching_configured_patterns(tmp_path):
    """Trailing slash in pattern filters configured patterns to those starting with the prefix."""
    category_dir = tmp_path / "policies"
    subdir = category_dir / "git" / "ops"
    subdir.mkdir(parents=True)
    (category_dir / "git" / "ops" / "conservative.md").write_text("# Conservative")
    (category_dir / "git" / "ops" / "agent-assisted.md").write_text("# Agent")
    (category_dir / "testing").mkdir(parents=True)
    (category_dir / "testing" / "strict.md").write_text("# Strict")

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
    result = await gather_category_fileinfos(
        await _request_context(tmp_path, session), project, "policies", patterns=["git/ops/"]
    )

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
    result = await gather_category_fileinfos(
        await _request_context(tmp_path, session), project, "policies", patterns=["git/ops/"]
    )

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
    result = await gather_category_fileinfos(
        await _request_context(tmp_path, session), project, "policies", patterns=["git/ops/conservative*"]
    )

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
    result = await gather_category_fileinfos(
        await _request_context(tmp_path, session), project, "policies", patterns=["git/ops/"]
    )

    assert len(result) == 2
    names = {r.name for r in result}
    assert names == {"git/ops/conservative.md", "git/ops/agent-assisted.md"}


# --- Tests for render_missing_policy ---


@pytest.mark.anyio
async def test_missing_policy_fallback_identifies_each_topic(tmp_path):
    """A missing template produces actionable, topic-specific fallback text."""
    context = await _request_context(tmp_path, _MockSession(""))
    for topic in ("git/ops", "testing"):
        assert await render_missing_policy(context, topic) == f"{INSTRUCTION_MISSING_POLICY}\n\nTopic: `{topic}`"


# --- Tests for _gather_policy_partials ---


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
    result = await _gather_policy_partials(
        await _request_context(tmp_path, _MockSession(str(tmp_path))), file_info, TemplateContext({}), {}
    )
    assert result == ({}, {}, {})


@pytest.mark.anyio
async def test_gather_policy_partials_unbound_session_returns_empty(tmp_path):
    """An explicit unbound session returns no policy partials."""
    policy_file = tmp_path / "doc.md.mustache"
    policy_file.write_text("---\npolicies:\n  - git/ops\n---\nContent.")

    file_info = FileInfo(
        path=policy_file,
        size=policy_file.stat().st_size,
        content_size=0,
        mtime=datetime(2024, 1, 1),
        name="doc.md",
    )

    result = await _gather_policy_partials(
        await _request_context(tmp_path, _MockSession(str(tmp_path))), file_info, TemplateContext({}), {}
    )
    assert result == ({}, {}, {})


@pytest.mark.anyio
async def test_gather_policy_partials_no_match_returns_placeholder(tmp_path, monkeypatch):
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
    (tmp_path / "policies" / "testing").mkdir(parents=True)
    (tmp_path / "policies" / "testing" / "strict.md").write_text("# Strict")
    session = _MockSession(str(tmp_path), project=project)
    result = await _gather_policy_partials(
        await _request_context(tmp_path, session), file_info, TemplateContext({}), {}
    )

    partials, frontmatter, cache_policies = result
    assert "git/ops" in partials
    assert INSTRUCTION_MISSING_POLICY in partials["git/ops"]
    assert "git/ops" in partials["git/ops"]
    assert frontmatter == {}
    assert cache_policies == {}


@pytest.mark.anyio
async def test_gather_policy_partials_matching_topic_renders_content(runtime, tmp_path):
    """Topic with a matching policy file → rendered content returned."""
    doc_file = tmp_path / "doc.md.mustache"
    doc_file.write_text("---\npolicies:\n  - git/ops\n---\nContent.")

    file_info = FileInfo(
        path=doc_file,
        size=doc_file.stat().st_size,
        content_size=0,
        mtime=datetime(2024, 1, 1),
        name="doc.md",
    )

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
    config = runtime.configuration_service().config_file
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    session = await create_bound_test_session(runtime, "policies")
    await session.update_config(lambda current: replace(current, categories=project.categories))
    result = await _gather_policy_partials(await request_context_for(session), file_info, TemplateContext({}), {})

    partials, frontmatter, cache_policies = result
    assert partials == {"git/ops": "Use conservative git ops."}
    assert frontmatter == {"git/ops": [{"type": "agent/instruction"}]}
    assert cache_policies["git/ops"] == [CachePolicy.long_public()]
