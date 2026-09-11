"""Tests for document cache policy frontmatter."""

from collections.abc import Iterable
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Self

import pytest

from mcp_guide.content.utils import resolve_content_cache_policy, resolve_file_cache_policy
from mcp_guide.render.cache_policy import CachePolicy, CacheScope
from mcp_guide.render.content import RenderedContent
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.document_properties import (
    DocumentContribution,
    DocumentDisposition,
    DocumentProperties,
    DocumentProperty,
)
from mcp_guide.render.frontmatter import Frontmatter
from mcp_guide.render.renderer import render_template_content


def _contribution(frontmatter: dict[str, object], *, cache_default: CachePolicy | None = None) -> DocumentContribution:
    return DocumentContribution(
        "partial content",
        frontmatter,
        DocumentProperties.from_frontmatter(frontmatter, cache_default=cache_default),
    )


def _parse_cache_policy(value: object) -> CachePolicy:
    """Parse cache frontmatter while disregarding diagnostics in assertions."""
    return CachePolicy.parse_with_diagnostic(value)[0]


class _TypeObserver(DocumentProperty):
    """Test-only property that shares the type frontmatter key."""

    def __init__(self) -> None:
        self.values: list[str] = []

    @classmethod
    def handles_frontmatter_key(cls, key: str) -> bool:
        return key == "type"

    def apply_frontmatter(self, key: str, value: Any) -> None:
        if isinstance(value, str):
            self.values.append(value)

    @classmethod
    def combine(cls, properties: Iterable[Self]) -> Self:
        combined = cls()
        combined.values = [value for property in properties for value in property.values]
        return combined


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
    assert _parse_cache_policy(value) == expected


def test_invalid_cache_policy_is_not_cacheable() -> None:
    """Malformed cache metadata must not accidentally enable caching."""
    policy, diagnostic = CachePolicy.parse_with_diagnostic("quick, shared")

    assert policy == CachePolicy.no_cache()
    assert diagnostic == "Invalid cache policy: 'quick, shared'"


def test_document_properties_broadcasts_shared_frontmatter_keys() -> None:
    """Multiple typed properties may consume the same frontmatter key."""
    observer = _TypeObserver()
    properties = DocumentProperties.from_frontmatter(
        {"type": "agent/instruction"},
        property_handlers=[DocumentDisposition(), observer],
    )

    assert properties.disposition == "agent/instruction"
    assert observer.values == ["agent/instruction"]


def test_combined_documents_use_the_most_restrictive_policy() -> None:
    """Partials can only reduce the cacheability of their parent document."""
    parent = _parse_cache_policy("long")
    partial = _parse_cache_policy("medium, private")

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
        partial_contributions=[_contribution({"cache": "short, private"})],
    )

    assert content.cache_policy == _parse_cache_policy("short, private")
    content.partial_contributions.append(_contribution({}))
    assert content.cache_policy == CachePolicy.no_cache()


def test_rendered_content_combines_partial_disposition(tmp_path) -> None:
    """A rendered partial may raise the disposition of its parent document."""
    content = RenderedContent(
        frontmatter=Frontmatter({"type": "user/information"}),
        frontmatter_length=0,
        content="Rendered",
        content_length=8,
        template_path=tmp_path / "document.md.mustache",
        template_name="document",
        partial_contributions=[_contribution({"type": "agent/instruction"})],
    )

    assert content.disposition == "agent/instruction"


@pytest.mark.anyio
async def test_pre_rendered_policy_partial_contributes_to_cache_policy(tmp_path) -> None:
    """A referenced policy partial participates in parent cache composition."""
    result = await render_template_content(
        "Parent {{> policy}}",
        TemplateContext({}),
        partials={"policy": "policy content"},
        pre_rendered_partial_contributions={"policy": [_contribution({"cache": "short, private"})]},
    )

    assert result.success
    assert result.value is not None
    content, partial_contributions, _ = result.value
    rendered = RenderedContent(
        frontmatter=Frontmatter({"cache": "long"}),
        frontmatter_length=0,
        content=content,
        content_length=len(content),
        template_path=tmp_path / "parent.mustache",
        template_name="parent",
        partial_contributions=partial_contributions,
    )

    assert rendered.cache_policy == _parse_cache_policy("short, private")


@pytest.mark.anyio
async def test_pre_rendered_policy_partial_contributes_to_disposition(tmp_path) -> None:
    """A referenced policy partial participates in parent disposition composition."""
    result = await render_template_content(
        "Parent {{> policy}}",
        TemplateContext({}),
        partials={"policy": "policy content"},
        pre_rendered_partial_contributions={"policy": [_contribution({"type": "agent/instruction"})]},
    )

    assert result.success
    assert result.value is not None
    content, partial_contributions, _ = result.value
    rendered = RenderedContent(
        frontmatter=Frontmatter({"type": "user/information"}),
        frontmatter_length=0,
        content=content,
        content_length=len(content),
        template_path=tmp_path / "parent.mustache",
        template_name="parent",
        partial_contributions=partial_contributions,
    )

    assert rendered.disposition == "agent/instruction"


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
    content, partial_contributions, _ = result.value
    rendered = RenderedContent(
        frontmatter=Frontmatter({"cache": "long"}),
        frontmatter_length=0,
        content=content,
        content_length=len(content),
        template_path=tmp_path / "parent.mustache",
        template_name="parent",
        partial_contributions=partial_contributions,
    )

    assert rendered.cache_policy == CachePolicy.no_cache()


@pytest.mark.anyio
async def test_pre_rendered_policy_uses_its_resolved_nested_policy(tmp_path) -> None:
    """A policy's nested no-cache contributor cannot be lost at its parent boundary."""
    result = await render_template_content(
        "Parent {{> policy}}",
        TemplateContext({}),
        partials={"policy": "policy content"},
        pre_rendered_partial_contributions={
            "policy": [
                DocumentContribution(
                    "policy content",
                    {"cache": "long"},
                    DocumentProperties.from_frontmatter(None),
                )
            ]
        },
    )

    assert result.success
    assert result.value is not None
    content, partial_contributions, _ = result.value
    rendered = RenderedContent(
        frontmatter=Frontmatter({"cache": "long"}),
        frontmatter_length=0,
        content=content,
        content_length=len(content),
        template_path=tmp_path / "parent.mustache",
        template_name="parent",
        partial_contributions=partial_contributions,
    )

    assert rendered.cache_policy == CachePolicy.no_cache()


def test_collected_content_uses_each_rendered_document_policy() -> None:
    """The aggregate policy preserves partial-aware document resolution."""
    files = [
        SimpleNamespace(cache_policy=_parse_cache_policy("long"), frontmatter={}),
        SimpleNamespace(cache_policy=_parse_cache_policy("short, private"), frontmatter={}),
    ]

    assert resolve_content_cache_policy(files) == _parse_cache_policy("short, private")


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
