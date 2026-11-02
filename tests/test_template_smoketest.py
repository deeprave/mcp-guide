"""Behavioural checks for the template inventory smoke test."""

import pytest
from scripts.template_smoketest import main


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("template", "expected_status"),
    [
        ("---\nrequires-hidden: true\n---\nNot applicable", 0),
        ("---\ndescription: '{{#_error}}Invalid template metadata{{/_error}}'\n---\nBody", 1),
    ],
    ids=["filtered-template", "render-diagnostic"],
)
async def test_smoketest_distinguishes_filtered_templates_from_render_diagnostics(
    tmp_path, template, expected_status
) -> None:
    """Filtering is expected, while a renderer diagnostic makes the inventory fail."""
    (tmp_path / "sample.mustache").write_text(template)

    assert await main(tmp_path, quiet=True) == expected_status
