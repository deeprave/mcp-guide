"""Integration test fixtures.

## MCP Server Factory Fixture

Tools are registered on server creation via deferred registration and require
fresh registration state between modules.

The mcp_server_factory fixture resets registration state and creates a fresh
server per module.
"""

from importlib import import_module

import pytest

from mcp_guide.server import create_server


@pytest.fixture(scope="module")
def mcp_server_factory(tmp_path_factory):
    """Factory to create MCP server with specified tool modules reloaded.

    Usage:
        @pytest.fixture(scope="module")
        def mcp_server(mcp_server_factory):
            return mcp_server_factory(["tool_category"])
    """
    from copy import deepcopy

    from mcp_guide.core import tool_decorator

    saved_registry = deepcopy(tool_decorator._TOOL_REGISTRY)

    def _create_server(tool_modules: list[str]):
        # Clear tool registration state before bootstrap so each fixture has
        # a deterministic, isolated set of registered tools.
        from mcp_guide.core.tool_decorator import clear_tool_registry

        clear_tool_registry()

        # Import (or reload) tool modules to repopulate decorator metadata after
        # the registry clear. Modules remain in memory once imported, so a
        # direct import is insufficient on subsequent invocations.
        import importlib
        import sys

        for module_name in tool_modules:
            full_name = f"mcp_guide.tools.{module_name}"
            if full_name in sys.modules:
                importlib.reload(sys.modules[full_name])
            else:
                import_module(full_name)

        # Create new server instance
        from mcp_guide.cli import ServerConfig
        from mcp_guide.runtime import get_runtime

        try:
            leftover = get_runtime()
        except RuntimeError:
            leftover = None
        if leftover is not None:
            if leftover.started:
                import anyio

                anyio.run(leftover.stop)
            else:
                leftover._release_process_runtime()
        isolated = tmp_path_factory.mktemp("mcp-server")
        docs = isolated / "docs"
        docs.mkdir()
        config = ServerConfig(configdir=str(isolated), docroot=str(docs))
        server = create_server(config)

        return server

    yield _create_server

    # Clean up after module
    from mcp_guide.core.tool_decorator import clear_tool_registry

    clear_tool_registry()
    tool_decorator._TOOL_REGISTRY.update(saved_registry)


@pytest.fixture
async def resource_project(runtime, tmp_path):
    """Real content and command fixtures shared by the two resource entry points."""
    import yaml

    from mcp_guide.models import Category
    from tests.helpers import create_bound_test_session, request_context_for

    docroot = tmp_path / "resource-docs"
    for folder in ("docs", "policies/git/ops", "_commands/project", "_commands/openspec"):
        (docroot / folder).mkdir(parents=True, exist_ok=True)
    (docroot / "docs/readme.md").write_text("docs content")
    (docroot / "policies/git/ops/rules.md").write_text("git policy")
    (docroot / "policies/other.md").write_text("unrelated policy")
    (docroot / "_commands/project/project.mustache").write_text(
        "---\naliases: ['project?verbose']\n---\n"
        "{{project.name}}{{#kwargs.verbose}} verbose{{/kwargs.verbose}}{{#kwargs.table}} table{{/kwargs.table}}"
    )
    (docroot / "_commands/openspec/show.mustache").write_text(
        "Show {{#args}}{{value}}{{/args}}{{#kwargs.verbose}} verbose{{/kwargs.verbose}}"
    )
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    session = await create_bound_test_session(runtime, "resource-project")
    for name, patterns in (("docs", ["*.md"]), ("policies", ["git/ops/*.md", "other.md"])):
        await session.update_config(
            lambda p, name=name, patterns=patterns: p.with_category(name, Category(dir=name, patterns=patterns))
        )
    return await request_context_for(session, "resource-session")
