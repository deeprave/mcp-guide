"""Behaviour tests for composed frontmatter-declared elicitation."""

from mcp_guide.render.cache_policy import CachePolicy
from mcp_guide.render.document_properties import DocumentCache, DocumentElicitation, DocumentProperties


def test_distinct_parent_and_partial_forms_combine() -> None:
    """Distinct forms from contributing documents remain available together."""
    parent = DocumentProperties.from_frontmatter(
        {"elicitation": {"target": {"schema": {"properties": {"mode": {"type": "string"}}}}}},
        source="parent command",
    )
    partial = DocumentProperties.from_frontmatter(
        {"elicitation": {"reference": {"schema": {"properties": {"reference": {"type": "string"}}}}}},
        source="reference partial",
    )

    combined = DocumentProperties.combine([parent, partial]).get(DocumentElicitation)

    assert set(combined.forms) == {"target", "reference"}
    assert combined.diagnostic is None


def test_duplicate_form_property_has_a_composition_diagnostic() -> None:
    """Contributors cannot silently introduce ambiguous input fields."""
    parent = DocumentProperties.from_frontmatter(
        {"elicitation": {"target": {"schema": {"properties": {"mode": {"type": "string"}}}}}},
        source="parent command",
    )
    partial = DocumentProperties.from_frontmatter(
        {"elicitation": {"reference": {"schema": {"properties": {"mode": {"type": "string"}}}}}},
        source="mode partial",
    )

    combined = DocumentProperties.combine([parent, partial]).get(DocumentElicitation)

    assert combined.diagnostic is not None
    assert "parent command" in combined.diagnostic
    assert "mode partial" in combined.diagnostic


def test_property_only_partial_retains_an_explicit_cache_policy() -> None:
    """Preflight delivery properties preserve an author's explicit cache restriction."""
    partial = DocumentProperties.from_frontmatter(
        {"cache": "short, private", "elicitation": {"target": {}}},
        source="property-only partial",
    )

    delivery = partial.preflight_delivery_properties()

    assert delivery.cache_policy == CachePolicy.parse("short, private")[0]


def test_property_only_partial_drops_its_implicit_no_cache_default() -> None:
    """A preflight-only implicit no-cache default must not alter delivery."""
    partial = DocumentProperties.from_frontmatter({"elicitation": {"target": {}}}, source="property-only partial")

    delivery = partial.preflight_delivery_properties()

    assert not any(isinstance(property, DocumentCache) for property in delivery.properties)


def test_form_only_partial_does_not_override_another_explicit_cache_policy() -> None:
    """Implicit preflight cache state never changes another contributor's delivery policy."""
    explicit = DocumentProperties.from_frontmatter(
        {"cache": "short, private", "elicitation": {"target": {}}},
        source="explicit partial",
    )
    form_only = DocumentProperties.from_frontmatter({"elicitation": {"reference": {}}}, source="form-only partial")

    delivery = DocumentProperties.combine(
        (explicit.preflight_delivery_properties(), form_only.preflight_delivery_properties())
    )

    assert delivery.cache_policy == CachePolicy.parse("short, private")[0]
