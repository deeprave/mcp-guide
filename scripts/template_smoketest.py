#!/usr/bin/env python3
"""Smoke-test shipped Guide templates with representative data.

Run with ``uv run python scripts/template_smoketest.py``.  This is a
repeatable compatibility check for renderer upgrades; it intentionally lives
outside pytest because it exercises the installed production template tree as
an inventory, rather than asserting source text in the normal test suite.
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp_guide.core.path_security import resolve_safe_path
from mcp_guide.discovery.files import TEMPLATE_EXTENSIONS
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import process_frontmatter
from mcp_guide.render.recommendations import Recommendation
from mcp_guide.render.renderer import render_template_content

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_ROOT = REPOSITORY_ROOT / "src" / "mcp_guide" / "templates"


async def _ignore_recommendation_footnotes(_: list[Recommendation]) -> str:
    """Enable recommendation syntax without needing a live session in this check."""
    return ""


def _context(values: Mapping[str, Any] | None = None) -> TemplateContext:
    """Return broadly representative context for the inventory smoke render."""
    base: dict[str, Any] = {
        "agent": {"prefix": "@", "name": "Example Agent"},
        "auth": {"active": False, "authenticated": True, "user": True, "admin": True},
        "args": [{"value": "discussion"}],
        "kwargs": {"table": False},
        "project": {"name": "example-project", "root": "/workspace/example-project"},
        "session": {"id": "example-session"},
        "workflow": {
            "file": ".guide.yaml",
            "phase": "discussion",
            "issue": "example-change",
            "queue": ["next-change"],
            "phase_list": ["exploration", "discussion", "implementation", "review"],
        },
        "openspec": {"available": True, "show": True},
        "feature_flags": {},
        "h1": "# ",
        "h2": "## ",
        "h3": "### ",
        "b": "**",
        "workflow-file": ".guide.yaml",
    }
    if values:
        base.update(values)
    return TemplateContext(base)


def _requirements_context() -> dict[str, Any]:
    """Return project flags that let the smoke test exercise gated templates."""
    return {
        "onboarded": False,
        "openspec": True,
        "python": ">=3.13",
        "workflow": True,
    }


def _resolver(template_root: Path, path: str | Path) -> Path:
    """Resolve a declared partial through the selected template document root."""
    return resolve_safe_path(template_root, path)


@dataclass(frozen=True)
class InventoryCase:
    """A representative output assertion for a shipped template."""

    template: str
    context: Mapping[str, Any]
    expected_fragments: tuple[str, ...]
    expected_frontmatter_fragments: Mapping[str, str] | None = None


CASES = (
    InventoryCase(
        template="_openspec/_error-format.mustache",
        context={
            "error": "The requested change is unavailable.",
            "message": "Choose an available change.",
            "available_changes": ["add-template-languages", "update-to-latest-chevron"],
        },
        expected_fragments=(
            "## OpenSpec Error",
            "The requested change is unavailable.",
            "- add-template-languages",
            "- update-to-latest-chevron",
        ),
    ),
    InventoryCase(
        template="_system/_startup.mustache",
        context={"workflow": False},
        expected_fragments=(
            "## How Guide talks to you",
            "Most Guide responses carry a `disposition`",
            "## Filesystem-sharing check",
        ),
    ),
    InventoryCase(
        template="docs/tracking.mustache",
        context={
            "workflow": {
                "file": ".guide.yaml",
                "phase_list": ["exploration", "discussion", "implementation"],
            },
        },
        expected_fragments=("phase: [exploration|discussion|implementation]",),
        expected_frontmatter_fragments={
            "instruction": "Read .guide.yaml directly; never discover it with a glob or search.",
        },
    ),
    InventoryCase(
        template="_commands/help.mustache",
        context={
            "args": [{"value": "help"}],
            "command_help": {
                "name": "help",
                "aliases": ["h", "commands"],
                "description": "Show available commands.",
                "usage": "guide://_help",
                "examples": ["guide://_help"],
            },
        },
        expected_fragments=("## help (`h`, `commands`)", "- `guide://_help`"),
    ),
)


def _template_paths(template_root: Path) -> list[Path]:
    """Discover all renderable templates under the selected document root."""
    return sorted(
        path for path in template_root.rglob("*") if path.is_file() and path.name.endswith(TEMPLATE_EXTENSIONS)
    )


@dataclass(frozen=True)
class SmokeRender:
    """Rendered content and processed frontmatter from the production path."""

    content: str
    frontmatter: Mapping[str, Any]
    errors: tuple[str, ...]


async def _render_template(
    path: Path,
    template_root: Path,
    values: Mapping[str, Any] | None = None,
) -> SmokeRender | None:
    """Run the production frontmatter, declared-partial, and body-rendering stages."""
    context = _context(values)
    requirements_context = _requirements_context()
    processed = await process_frontmatter(
        path.read_text(encoding="utf-8"),
        requirements_context,
        context,
    )
    if processed is None:
        return None

    frontmatter_variables = {
        key: value
        for key, value in processed.frontmatter.items()
        if not key.startswith("requires-") and key != "includes"
    }
    if frontmatter_variables:
        context = context.new_child(frontmatter_variables)

    result = await render_template_content(
        processed.content,
        context,
        file_path=path.relative_to(template_root).as_posix(),
        metadata=dict(processed.frontmatter),
        requirements_context=requirements_context,
        base_dir=path.parent,
        resolver=lambda partial_path: _resolver(template_root, partial_path),
        recommendation_footnotes=_ignore_recommendation_footnotes,
    )
    if not result.success or result.value is None:
        raise RuntimeError(result.error or "render produced no value")
    return SmokeRender(
        result.value.content,
        processed.frontmatter,
        tuple((*processed.errors, *result.value.errors)),
    )


async def _render_inventory(template_root: Path, *, verbose: bool) -> list[str]:
    """Render every shipped template and its declared partials once."""
    failures: list[str] = []
    for path in _template_paths(template_root):
        try:
            rendered = await _render_template(path, template_root)
            if rendered is not None:
                failures.extend(f"{path.relative_to(template_root)}: {error}" for error in rendered.errors)
            if verbose:
                print(path.relative_to(template_root))
        except Exception as error:
            failures.append(f"{path.relative_to(template_root)}: {error}")
    return failures


async def _verify_cases(template_root: Path) -> tuple[list[str], int]:
    """Render representative production templates and check their output."""
    failures: list[str] = []
    cases_run = 0
    for case in CASES:
        path = template_root / case.template
        if not path.is_file():
            continue
        cases_run += 1
        try:
            result = await _render_template(path, template_root, case.context)
        except Exception as error:
            failures.append(f"{case.template}: {error}")
            continue
        if result is None:
            failures.append(f"{case.template}: unexpectedly filtered by frontmatter requirements")
            continue
        for fragment in case.expected_fragments:
            if fragment not in result.content:
                failures.append(f"{case.template}: expected output fragment was absent: {fragment!r}")
        for field, fragment in (case.expected_frontmatter_fragments or {}).items():
            value = result.frontmatter.get(field)
            if not isinstance(value, str) or fragment not in value:
                failures.append(f"{case.template}: expected frontmatter fragment was absent: {field}={fragment!r}")
    return failures, cases_run


def _document_root(value: str) -> Path:
    """Validate an explicitly supplied template document root."""
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"document path is not a directory: {path}")
    return path


def _parse_args() -> argparse.Namespace:
    """Parse the smoke-test command-line options."""
    parser = argparse.ArgumentParser(description="Render and check Guide templates under a document root.")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("-v", "--verbose", action="store_true", help="Display each rendered template path.")
    output.add_argument("-q", "--quiet", action="store_true", help="Suppress all output; rely on the exit status.")
    parser.add_argument(
        "document_path",
        nargs="?",
        metavar="<document-path>",
        type=_document_root,
        help=f"Template document root to scan (default: {DEFAULT_TEMPLATE_ROOT}).",
    )
    return parser.parse_args()


async def main(
    document_path: Path | None = None,
    *,
    verbose: bool = False,
    quiet: bool = False,
) -> int:
    """Run the bulk smoke render and representative output checks."""
    template_root = document_path or DEFAULT_TEMPLATE_ROOT
    templates = _template_paths(template_root)
    case_failures, cases_run = await _verify_cases(template_root)
    failures = [*(await _render_inventory(template_root, verbose=verbose)), *case_failures]
    if not templates:
        failures.append(f"{template_root}: no renderable templates found")
    if failures:
        if not quiet:
            print(f"Template smoke test failed ({len(failures)} issue(s)):")
            for failure in failures:
                print(f"- {failure}")
        return 1
    if not quiet:
        print(f"Template smoke test passed: {len(templates)} templates and {cases_run} representative cases.")
    return 0


if __name__ == "__main__":
    arguments = _parse_args()
    raise SystemExit(asyncio.run(main(arguments.document_path, verbose=arguments.verbose, quiet=arguments.quiet)))
