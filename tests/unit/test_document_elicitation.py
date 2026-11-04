"""Behaviour tests for composed frontmatter-declared elicitation."""

from mcp_guide.render.document_properties import DocumentElicitation, DocumentProperties


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


def test_property_only_partial_keeps_its_elicitation() -> None:
    """A cache declaration does not prevent preflight form discovery."""
    partial = DocumentProperties.from_frontmatter(
        {"cache": "short, private", "elicitation": {"target": {}}},
        source="property-only partial",
    )

    assert set(partial.elicitation.forms) == {"target"}


def test_property_only_partial_discovers_elicitation_without_a_cache() -> None:
    """A form remains discoverable without an explicit cache declaration."""
    partial = DocumentProperties.from_frontmatter({"elicitation": {"target": {}}}, source="property-only partial")

    assert set(partial.elicitation.forms) == {"target"}


def test_form_only_partials_combine_elicitations() -> None:
    """Form-only contributors combine their inputs without delivery composition."""
    first = DocumentProperties.from_frontmatter(
        {"cache": "short, private", "elicitation": {"target": {"schema": {"properties": {"target": {}}}}}},
        source="first partial",
    )
    second = DocumentProperties.from_frontmatter(
        {"elicitation": {"reference": {"schema": {"properties": {"reference": {}}}}}},
        source="second partial",
    )

    combined = DocumentProperties.combine((first, second))

    assert set(combined.elicitation.forms) == {"target", "reference"}


def test_source_on_a_non_string_property_has_a_composition_diagnostic() -> None:
    """Dynamic choices are text, so a source on any other property type is an authoring error."""
    command = DocumentProperties.from_frontmatter(
        {"elicitation": {"target": {"schema": {"properties": {"count": {"type": "integer", "source": "x"}}}}}},
        source="count command",
    )

    combined = DocumentProperties.combine([command]).get(DocumentElicitation)

    assert combined.diagnostic is not None
    assert "count" in combined.diagnostic
    assert "count command" in combined.diagnostic
    assert combined.forms == {}
