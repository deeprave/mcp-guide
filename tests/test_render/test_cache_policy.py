"""Tests for document cache policy frontmatter."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_guide.content.utils import resolve_content_cache_policy, resolve_file_cache_policy
from mcp_guide.render.cache_policy import CachePolicy, CacheScope
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import Frontmatter
from mcp_guide.render.renderer import render_template_content


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("long", CachePolicy(86_400_000, CacheScope.PUBLIC)),
        ("medium, private", CachePolicy(900_000, CacheScope.PRIVATE)),
        ("short, public", CachePolicy(120_000, CacheScope.PUBLIC)),
        ("medium, shared", CachePolicy(900_000, CacheScope.PUBLIC)),
        ("public", CachePolicy(900_000, CacheScope.PUBLIC)),
        ("none", CachePolicy.no_cache()),
        ("no-cache", CachePolicy.no_cache()),
        (None, CachePolicy.no_cache()),
    ],
)
def test_parse_cache_policy(value: object, expected: CachePolicy) -> None:
    """Frontmatter cache syntax resolves to the documented policy."""
    assert CachePolicy.parse(value) == expected


def test_invalid_cache_policy_is_not_cacheable() -> None:
    """Malformed cache metadata must not accidentally enable caching."""
    policy, diagnostic = CachePolicy.parse_with_diagnostic("quick, shared")

    assert policy == CachePolicy.no_cache()
    assert diagnostic == "Invalid cache policy: 'quick, shared'"


def test_combined_documents_use_the_most_restrictive_policy() -> None:
    """Partials can only reduce the cacheability of their parent document."""
    parent = CachePolicy.parse("long")
    partial = CachePolicy.parse("medium, private")

    assert parent >= partial
    assert partial <= parent
    assert CachePolicy.combine((parent, partial)) == partial
    assert CachePolicy.combine((parent, CachePolicy.no_cache())) == CachePolicy.no_cache()


def test_rendered_content_combines_partial_cache_policies(tmp_path) -> None:
    """A partial without a declaration prevents caching the combined result."""
    content = RenderedContent(
        frontmatter=Frontmatter({"cache": "long"}),
        frontmatter_length=0,
        content="Rendered",
        content_length=8,
        template_path=tmp_path / "document.md.mustache",
        template_name="document",
        partial_frontmatter=[{"cache": "short, private"}],
        partial_cache_policies=[CachePolicy.parse("short, private")],
    )

    assert content.cache_policy == CachePolicy.parse("short, private")
    content.partial_cache_policies.append(CachePolicy.no_cache())
    assert content.cache_policy == CachePolicy.no_cache()


@pytest.mark.anyio
async def test_pre_rendered_policy_partial_contributes_to_cache_policy(tmp_path) -> None:
    """A referenced policy partial participates in parent cache composition."""
    result = await render_template_content(
        "Parent {{> policy}}",
        TemplateContext({}),
        partials={"policy": "policy content"},
        pre_rendered_partial_frontmatter={"policy": [{"cache": "short, private"}]},
        pre_rendered_partial_cache_policies={"policy": [CachePolicy.parse("short, private")]},
    )

    assert result.success
    assert result.value is not None
    content, partial_frontmatter, partial_cache_policies, _ = result.value
    rendered = RenderedContent(
        frontmatter=Frontmatter({"cache": "long"}),
        frontmatter_length=0,
        content=content,
        content_length=len(content),
        template_path=tmp_path / "parent.mustache",
        template_name="parent",
        partial_frontmatter=partial_frontmatter,
        partial_cache_policies=partial_cache_policies,
    )

    assert rendered.cache_policy == CachePolicy.parse("short, private")


@pytest.mark.anyio
async def test_undeclared_pre_rendered_partial_disables_parent_caching(tmp_path) -> None:
    """An accessed partial without policy metadata is an implicit no-cache contributor."""
    result = await render_template_content(
        "Parent {{> policy}}",
        TemplateContext({}),
        partials={"policy": "policy content"},
    )

    assert result.success
    assert result.value is not None
    content, partial_frontmatter, partial_cache_policies, _ = result.value
    rendered = RenderedContent(
        frontmatter=Frontmatter({"cache": "long"}),
        frontmatter_length=0,
        content=content,
        content_length=len(content),
        template_path=tmp_path / "parent.mustache",
        template_name="parent",
        partial_frontmatter=partial_frontmatter,
        partial_cache_policies=partial_cache_policies,
    )

    assert rendered.cache_policy == CachePolicy.no_cache()


@pytest.mark.anyio
async def test_pre_rendered_policy_uses_its_resolved_nested_policy(tmp_path) -> None:
    """A policy's nested no-cache contributor cannot be lost at its parent boundary."""
    result = await render_template_content(
        "Parent {{> policy}}",
        TemplateContext({}),
        partials={"policy": "policy content"},
        pre_rendered_partial_frontmatter={"policy": [{"cache": "long"}]},
        pre_rendered_partial_cache_policies={"policy": [CachePolicy.no_cache()]},
    )

    assert result.success
    assert result.value is not None
    content, partial_frontmatter, partial_cache_policies, _ = result.value
    rendered = RenderedContent(
        frontmatter=Frontmatter({"cache": "long"}),
        frontmatter_length=0,
        content=content,
        content_length=len(content),
        template_path=tmp_path / "parent.mustache",
        template_name="parent",
        partial_frontmatter=partial_frontmatter,
        partial_cache_policies=partial_cache_policies,
    )

    assert rendered.cache_policy == CachePolicy.no_cache()


def test_collected_content_uses_each_rendered_document_policy() -> None:
    """The aggregate policy preserves partial-aware document resolution."""
    files = [
        SimpleNamespace(cache_policy=CachePolicy.parse("long"), frontmatter={}),
        SimpleNamespace(cache_policy=CachePolicy.parse("short, private"), frontmatter={}),
    ]

    assert resolve_content_cache_policy(files) == CachePolicy.parse("short, private")


def test_requirement_filtered_markdown_defaults_to_no_cache() -> None:
    """Requirement-filtered Markdown is dynamic unless it declares a policy."""
    file_info = SimpleNamespace(path=Path("document.md"), frontmatter={"requires-example": True})

    policy, diagnostic = resolve_file_cache_policy(file_info)

    assert policy == CachePolicy.no_cache()
    assert diagnostic is None


def test_invalid_rendered_cache_policy_is_diagnostic_and_not_cacheable(tmp_path, caplog) -> None:
    """Malformed declarations are visible to authors without blocking rendering."""
    content = RenderedContent(
        frontmatter=Frontmatter({"cache": "forever, shared"}),
        frontmatter_length=0,
        content="Still rendered",
        content_length=14,
        template_path=tmp_path / "document.md.mustache",
        template_name="document",
    )

    assert content.cache_policy == CachePolicy.no_cache()
    assert "Invalid cache policy" in caplog.text
