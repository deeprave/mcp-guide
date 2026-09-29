"""Tests for partial frontmatter handling."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.core.path_security import resolve_safe_path
from mcp_guide.discovery.files import FileInfo
from mcp_guide.render.cache_policy import CachePolicy
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import Frontmatter
from mcp_guide.render.partials import UnsafePartialPathError, load_partial_content
from mcp_guide.render.renderer import render_template_content
from mcp_guide.render.template import collect_interactive_document_properties


def document_root_resolver(document_root: Path):
    """Return the server-side containment resolver used by partial tests."""
    return lambda path: resolve_safe_path(document_root, path)


@pytest.mark.anyio
async def test_interactive_partial_load_errors_are_logged_without_hiding_composition_diagnostics(
    tmp_path, caplog
) -> None:
    """An unavailable listed partial is logged while valid contributors still compose."""
    parent = tmp_path / "parent.mustache"
    parent.write_text(
        "---\n"
        "includes: [first, missing]\n"
        "elicitation:\n"
        "  target:\n"
        "    message: Choose target.\n"
        "    schema:\n"
        "      type: object\n"
        "      properties:\n"
        "        mode:\n"
        "          type: string\n"
        "      required: [mode]\n"
        "---\n"
        "Parent"
    )
    (tmp_path / "_first.mustache").write_text(
        "---\n"
        "elicitation:\n"
        "  target:\n"
        "    message: Duplicate target.\n"
        "    schema:\n"
        "      type: object\n"
        "      properties:\n"
        "        reference:\n"
        "          type: string\n"
        "      required: [reference]\n"
        "---\n"
    )
    stat = parent.stat()
    file_info = FileInfo(parent, stat.st_size, stat.st_size, datetime.fromtimestamp(stat.st_mtime), parent.name)

    properties = await collect_interactive_document_properties(
        file_info,
        project_flags={},
        context=TemplateContext({}),
        resolver=document_root_resolver(tmp_path),
    )

    assert properties is not None
    assert properties.elicitation.diagnostic is not None
    assert "declared by both" in properties.elicitation.diagnostic
    assert "parent.mustache" in properties.elicitation.diagnostic
    assert str(tmp_path) not in properties.elicitation.diagnostic
    assert "Listed interactive partial could not be loaded" not in properties.elicitation.diagnostic
    assert any("missing" in record.message for record in caplog.records)


@pytest.mark.anyio
async def test_interactive_delivery_properties_preserve_static_values(tmp_path) -> None:
    """The parent and listed partials contribute static delivery properties."""
    parent = tmp_path / "parent.mustache"
    parent.write_text("---\ncache: short, private\nincludes: [input]\n---\nParent")
    (tmp_path / "_input.mustache").write_text("---\ncache: short, private\n---\n")
    stat = parent.stat()
    file_info = FileInfo(parent, stat.st_size, stat.st_size, datetime.fromtimestamp(stat.st_mtime), parent.name)

    properties = await collect_interactive_document_properties(
        file_info,
        project_flags={},
        context=TemplateContext({}),
        resolver=document_root_resolver(tmp_path),
    )

    assert properties is not None
    assert properties.delivery_properties is not None
    assert properties.delivery_properties.cache_policy == CachePolicy.parse("short, private")[0]


@pytest.mark.anyio
async def test_interactive_preflight_preserves_structural_parent_values_for_partial_elicitation(tmp_path) -> None:
    """Partial forms see literal structural parent values, not a preflight-only variant."""
    parent = tmp_path / "parent.mustache"
    parent.write_text("---\nparent-label: '{{workflow.name}}'\nincludes: [input]\n---\nParent")
    (tmp_path / "_input.mustache").write_text(
        "---\n"
        "elicitation:\n"
        "  target:\n"
        "    message: 'Choose {{parent-label}}.'\n"
        "    schema:\n"
        "      type: object\n"
        "      properties:\n"
        "        target:\n"
        "          type: string\n"
        "      required: [target]\n"
        "---\n"
    )
    stat = parent.stat()
    file_info = FileInfo(parent, stat.st_size, stat.st_size, datetime.fromtimestamp(stat.st_mtime), parent.name)

    properties = await collect_interactive_document_properties(
        file_info,
        project_flags={},
        context=TemplateContext({"workflow": {"name": "review"}}),
        resolver=document_root_resolver(tmp_path),
    )

    assert properties is not None
    assert properties.elicitation.forms["target"]["message"] == "Choose {{workflow.name}}."


@pytest.mark.anyio
async def test_malformed_interactive_includes_are_logged_and_ignored(tmp_path, caplog) -> None:
    """A malformed includes value remains a tolerant authoring error."""
    parent = tmp_path / "parent.mustache"
    parent.write_text("---\nincludes: invalid\n---\nParent")
    stat = parent.stat()
    file_info = FileInfo(parent, stat.st_size, stat.st_size, datetime.fromtimestamp(stat.st_mtime), parent.name)

    properties = await collect_interactive_document_properties(
        file_info,
        project_flags={},
        context=TemplateContext({}),
        resolver=document_root_resolver(tmp_path),
    )

    assert properties is not None
    assert not properties.elicitation.forms
    assert any("includes" in record.message for record in caplog.records)


@pytest.mark.anyio
async def test_form_only_partial_preserves_another_partial_explicit_cache_policy(tmp_path) -> None:
    """Only explicit property-only cache declarations reach the delivered document."""
    parent = tmp_path / "parent.mustache"
    parent.write_text("---\nincludes: [cached, form]\n---\nParent")
    (tmp_path / "_cached.mustache").write_text(
        "---\ncache: short, private\nelicitation:\n  target:\n    message: Choose target.\n"
        "    schema:\n      type: object\n      properties:\n        target:\n          type: string\n      required: [target]\n---\n"
    )
    (tmp_path / "_form.mustache").write_text(
        "---\nelicitation:\n  reference:\n    message: Choose reference.\n"
        "    schema:\n      type: object\n      properties:\n        reference:\n          type: string\n      required: [reference]\n---\n"
    )
    stat = parent.stat()
    file_info = FileInfo(parent, stat.st_size, stat.st_size, datetime.fromtimestamp(stat.st_mtime), parent.name)

    properties = await collect_interactive_document_properties(
        file_info,
        project_flags={},
        context=TemplateContext({}),
        resolver=document_root_resolver(tmp_path),
    )

    assert properties is not None
    assert properties.delivery_properties is not None
    assert properties.delivery_properties.cache_policy == CachePolicy.parse("short, private")[0]


@pytest.mark.anyio
class TestPartialFrontmatter:
    """Test partial loading with frontmatter."""

    async def test_load_partial_returns_frontmatter(self, tmp_path):
        """Test that load_partial_content returns frontmatter."""
        partial_file = tmp_path / "_test.mustache"
        partial_file.write_text("---\ntype: user/information\ninstruction: '^ Display this'\n---\nContent here")

        content, frontmatter = await load_partial_content(
            partial_file, tmp_path, resolver=document_root_resolver(tmp_path)
        )
        assert content == "Content here"
        assert isinstance(frontmatter, Frontmatter)
        assert frontmatter.get("type") == "user/information"
        assert frontmatter.get("instruction") == "^ Display this"

    async def test_load_partial_without_frontmatter(self, tmp_path):
        """Test partial without frontmatter returns empty dict."""
        partial_file = tmp_path / "_test.mustache"
        partial_file.write_text("Just content")

        content, frontmatter = await load_partial_content(
            partial_file, tmp_path, resolver=document_root_resolver(tmp_path)
        )
        assert content == "Just content"
        assert isinstance(frontmatter, Frontmatter)
        assert len(frontmatter) == 0

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

        content, _ = await load_partial_content(
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
        content, frontmatter = await load_partial_content(
            partial_file, tmp_path, context, resolver=document_root_resolver(tmp_path)
        )
        assert content == "Content"
        assert frontmatter.get("instruction") == "Show this"

    async def test_load_partial_with_requirements_not_met(self, tmp_path):
        """Test partial with unmet requirements returns empty content."""
        partial_file = tmp_path / "_test.mustache"
        partial_file.write_text("---\nrequires-feature: true\ninstruction: Show this\n---\nContent")

        context = {"feature": False}
        content, frontmatter = await load_partial_content(
            partial_file, tmp_path, context, resolver=document_root_resolver(tmp_path)
        )
        assert content == ""
        # Frontmatter should still be returned even if requirements not met
        assert frontmatter.get("instruction") == "Show this"


@pytest.mark.anyio
async def test_partial_regular_instruction_does_not_override_parent(tmp_path):
    """Test that partial with regular instruction does not override parent instruction."""

    # Create parent template with regular instruction
    parent_content = "{{>child}}"
    parent_metadata = Frontmatter({"instruction": "Parent instruction"})

    # Create partial with regular (non-important) instruction
    partial_path = tmp_path / "_child.mustache"
    partial_path.write_text("---\ninstruction: 'Child regular instruction'\n---\nChild content")

    # Render with includes
    parent_metadata["includes"] = ["child"]
    result = await render_template_content(
        parent_content,
        {},
        file_path=str(tmp_path / "parent.mustache"),
        metadata=parent_metadata,
        base_dir=tmp_path,
        resolver=document_root_resolver(tmp_path),
    )

    assert result.is_ok()
    # Parent metadata should NOT be changed by child's regular instruction
    assert parent_metadata["instruction"] == "Parent instruction"


@pytest.mark.anyio
async def test_partial_instruction_rendered_with_context(tmp_path):
    """Test that partial instruction/description fields are rendered as templates."""
    partial_file = tmp_path / "_test.mustache"
    partial_file.write_text("---\ninstruction: 'Hello {{name}}'\ndescription: 'Project {{project}}'\n---\nContent")

    context = {"name": "World", "project": "test"}
    content, frontmatter = await load_partial_content(
        partial_file, tmp_path, context, resolver=document_root_resolver(tmp_path)
    )

    assert content == "Content"
    assert frontmatter.get("instruction") == "Hello World"
    assert frontmatter.get("description") == "Project test"


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
async def test_used_partial_instruction_is_applied(tmp_path):
    """Partial instruction IS applied when partial is actually rendered via {{>partial}}."""

    # Template DOES reference {{>client-info}}
    template_content = "Status: {{>client-info}}"

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
    assert "Agent detection required" in rendered_content
    # Partial WAS rendered, so its frontmatter must be collected
    assert len(partial_contributions) == 1
    assert partial_contributions[0].frontmatter.get("instruction") == "^ Run client_info tool"


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


@pytest.mark.anyio
async def test_partial_instruction_placeholders_resolved(tmp_path):
    """Bug fix: placeholders like {{tool_prefix}} in partial instructions must be resolved."""

    template_content = "{{>agent-detect}}"

    partial_path = tmp_path / "_agent-detect.mustache"
    partial_path.write_text(
        "---\ntype: agent/instruction\ninstruction: 'Run {{tool_prefix}}client_info'\n---\nDetect agent"
    )

    metadata = Frontmatter({"includes": ["agent-detect"]})
    context = TemplateContext({"tool_prefix": "my_"})

    result = await render_template_content(
        template_content,
        context,
        file_path=str(tmp_path / "parent.mustache"),
        metadata=dict(metadata),
        base_dir=tmp_path,
        resolver=document_root_resolver(tmp_path),
    )

    assert result.is_ok()
    partial_contributions = result.value.partial_contributions
    assert len(partial_contributions) == 1
    # Placeholder must be resolved
    assert partial_contributions[0].frontmatter.get("instruction") == "Run my_client_info"


@pytest.mark.anyio
async def test_unsafe_partial_is_omitted_without_suppressing_safe_partial(tmp_path, caplog):
    """An unsafe partial is excluded while safe parent output remains available."""
    document_root = tmp_path / "docs"
    document_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (document_root / "_safe.mustache").write_text("safe content")
    (outside / "_secret.mustache").write_text("outside sentinel")

    result = await render_template_content(
        "parent {{>safe}} {{>secret}}",
        TemplateContext({}),
        file_path=str(document_root / "parent.mustache"),
        metadata={"includes": ["safe", "../outside/secret"]},
        base_dir=document_root,
        resolver=document_root_resolver(document_root),
    )

    assert result.is_ok()
    assert result.value.content == "parent safe content "
    assert "outside sentinel" not in result.value.content
    assert any("Unsafe partial reference omitted" in message for message in caplog.messages)
