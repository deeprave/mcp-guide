"""Tests for partial frontmatter handling."""

from pathlib import Path

import pytest

from mcp_guide.core.path_security import resolve_safe_path
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import Frontmatter
from mcp_guide.render.partials import UnsafePartialPathError, load_partial_content
from mcp_guide.render.renderer import render_template_content


def document_root_resolver(document_root: Path):
    """Return the server-side containment resolver used by partial tests."""
    return lambda path: resolve_safe_path(document_root, path)


@pytest.mark.anyio
class TestPartialFrontmatter:
    """Test partial loading with frontmatter."""

    async def test_load_partial_returns_frontmatter(self, tmp_path):
        """Test that load_partial_content returns frontmatter."""
        partial_file = tmp_path / "_test.mustache"
        partial_file.write_text("---\ntype: user/information\ninstruction: '^ Display this'\n---\nContent here")

        content, frontmatter, errors = await load_partial_content(
            partial_file, tmp_path, resolver=document_root_resolver(tmp_path)
        )
        assert content == "Content here"
        assert isinstance(frontmatter, Frontmatter)
        assert frontmatter.get("type") == "user/information"
        assert frontmatter.get("instruction") == "^ Display this"
        assert errors == []

    async def test_load_partial_rejects_symlink_escape(self, tmp_path):
        """An in-root partial symlink may not target content outside docroot."""
        document_root = tmp_path / "docs"
        document_root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "_secret.mustache").write_text("outside sentinel")
        (document_root / "_secret.mustache").symlink_to(outside / "_secret.mustache")

        with pytest.raises(UnsafePartialPathError, match="document root"):
            await load_partial_content(
                Path("_secret"),
                document_root,
                resolver=document_root_resolver(document_root),
            )

    async def test_load_partial_rejects_canonicalisation_failure(self, tmp_path, monkeypatch):
        """A canonicalisation failure is handled as an unsafe partial reference."""
        partial_file = tmp_path / "_loop.mustache"
        partial_file.write_text("unreachable")
        original_resolve = Path.resolve

        def raise_for_partial(path, *args, **kwargs):
            if path == partial_file:
                raise RuntimeError("symlink loop")
            return original_resolve(path, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", raise_for_partial)

        with pytest.raises(UnsafePartialPathError, match="document root"):
            await load_partial_content(
                Path("_loop"),
                tmp_path,
                resolver=document_root_resolver(tmp_path),
            )

    async def test_load_partial_ignores_directory_candidates(self, tmp_path):
        """A directory must not mask an extension-backed partial file."""
        (tmp_path / "_child").mkdir()
        (tmp_path / "_child.mustache").write_text("partial content")

        content, _, _ = await load_partial_content(
            Path("_child"),
            tmp_path,
            resolver=document_root_resolver(tmp_path),
        )

        assert content == "partial content"

    async def test_load_user_anchored_partial_is_rejected(self, tmp_path, monkeypatch):
        """A partial reference must not expand a server user home path."""
        home = tmp_path / "home"
        home.mkdir()
        partial_file = home / "_test.mustache"
        partial_file.write_text("User-anchored content")
        monkeypatch.setenv("HOME", str(home))

        with pytest.raises(UnsafePartialPathError, match="home-anchored"):
            await load_partial_content(Path("~/_test.mustache"), tmp_path)

    async def test_load_environment_variable_partial_is_rejected(self, tmp_path):
        """A partial reference must not expand environment variables."""
        with pytest.raises(UnsafePartialPathError, match="environment-variable"):
            await load_partial_content(Path("${HOME}/_test.mustache"), tmp_path)

    async def test_load_partial_with_requirements_met(self, tmp_path):
        """Test partial with met requirements returns content and frontmatter."""
        partial_file = tmp_path / "_test.mustache"
        partial_file.write_text("---\nrequires-feature: true\ninstruction: Show this\n---\nContent")

        context = {"feature": True}
        content, frontmatter, errors = await load_partial_content(
            partial_file, tmp_path, context, resolver=document_root_resolver(tmp_path)
        )
        assert content == "Content"
        assert frontmatter.get("instruction") == "Show this"
        assert errors == []

    async def test_load_partial_with_requirements_not_met(self, tmp_path):
        """Test partial with unmet requirements returns empty content."""
        partial_file = tmp_path / "_test.mustache"
        partial_file.write_text("---\nrequires-feature: true\ninstruction: Show this\n---\nContent")

        context = {"feature": False}
        content, frontmatter, errors = await load_partial_content(
            partial_file, tmp_path, context, resolver=document_root_resolver(tmp_path)
        )
        assert content == ""
        # A filtered partial is invisible to downstream render consumers.
        assert frontmatter == {}
        assert errors == []


@pytest.mark.anyio
async def test_partial_frontmatter_errors_propagate_to_parent_render(tmp_path):
    """A declared partial's frontmatter diagnostics reach the parent result."""
    (tmp_path / "_child.mustache").write_text(
        "---\ninstruction: '{{#_error}}Partial configuration is invalid{{/_error}}'\n---\nChild"
    )

    result = await render_template_content(
        "{{>child}}",
        {},
        file_path=str(tmp_path / "parent.mustache"),
        metadata=Frontmatter({"includes": ["child"]}),
        base_dir=tmp_path,
        resolver=document_root_resolver(tmp_path),
    )

    assert result.is_ok()
    assert result.value is not None
    assert result.value.content == "Child"
    assert result.value.errors == ["Partial 'child': Frontmatter field 'instruction': Partial configuration is invalid"]


@pytest.mark.anyio
async def test_unused_partial_instruction_not_applied(tmp_path):
    """Bug fix: partial instruction must NOT be applied when partial isn't rendered.

    If a partial is in the includes list but {{>partial}} is not in the template body,
    chevron never renders it, so its frontmatter should not be collected.
    """

    # Template does NOT reference {{>client-info}}
    template_content = "Status: OK"

    # Partial with important instruction exists in includes
    partial_path = tmp_path / "_client-info.mustache"
    partial_path.write_text(
        "---\ntype: agent/instruction\ninstruction: '^ Run client_info tool'\n---\nAgent detection required"
    )

    metadata = Frontmatter({"type": "user/information", "includes": ["client-info"]})
    context = TemplateContext({})

    result = await render_template_content(
        template_content,
        context,
        file_path=str(tmp_path / "status.mustache"),
        metadata=dict(metadata),
        base_dir=tmp_path,
        resolver=document_root_resolver(tmp_path),
    )

    assert result.is_ok()
    rendered_content = result.value.content
    partial_contributions = result.value.partial_contributions
    assert rendered_content == "Status: OK"
    # Partial was NOT rendered, so its frontmatter must NOT be in the list
    assert partial_contributions == []


@pytest.mark.anyio
async def test_requirement_gated_partial_retains_the_full_template_context(tmp_path):
    """Partial requirements use flags without discarding parent render variables."""
    (tmp_path / "_policy.mustache").write_text("---\nrequires-mcp-skills: true\n---\n{{workflow.name}}")

    result = await render_template_content(
        "{{>policy}}",
        TemplateContext({"workflow": {"name": "current-workflow"}}),
        file_path=str(tmp_path / "parent.mustache"),
        metadata={"includes": ["policy"]},
        requirements_context={"mcp-skills": True},
        base_dir=tmp_path,
        resolver=document_root_resolver(tmp_path),
    )

    assert result.success
    assert result.value is not None
    assert result.value.content == "current-workflow"
