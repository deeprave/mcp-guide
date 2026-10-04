"""Export delivery respects configured destinations without tracking client files."""

import json
from dataclasses import replace

import pytest
import yaml
from fastmcp import FastMCP
from fastmcp.client import Client, FastMCPTransport

from mcp_guide.auth import AuthScope, AuthService, UserAuthorisation, bind_user_authorisation
from mcp_guide.core.tool_decorator import register_tools
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.validators import registered_flag_names
from mcp_guide.models import Category
from mcp_guide.resources import guide_resource
from mcp_guide.result_constants import ERROR_SECURITY
from mcp_guide.tools.tool_content import ContentArgs, ExportContentArgs, export_content, internal_get_content
from mcp_guide.tools.tool_project import SetCurrentProjectArgs
from mcp_guide.tools.tool_resource import ReadResourceArgs, internal_read_resource
from tests.conftest import call_mcp_tool
from tests.helpers import (
    bind_isolated_test_session,
    create_bound_test_session,
    request_context_for,
    tool_result_payload,
)


@pytest.fixture
async def export_session(runtime, tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "readme.md").write_text("Current server content")
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    session = await create_bound_test_session(runtime, "stateless-export")
    await session.update_config(
        lambda p: replace(
            p.with_category("docs", Category(dir="docs", patterns=["*.md"])),
            allowed_write_paths=["exports/", "single"],
        )
    )
    return session


@pytest.mark.anyio
class TestStatelessExport:
    async def test_discovery_exposes_export_without_tracking_interfaces(self):
        server = FastMCP("stateless-export-discovery")
        register_tools(server)
        names = {tool.name for tool in await server.list_tools()}
        assert "export_content" in names
        assert names.isdisjoint({"list_exports", "remove_export"})
        assert "path-export" not in registered_flag_names()

    @pytest.mark.parametrize(
        "path,destination",
        [
            ("exports/report.md", "exports/report.md"),
            ("single", "single"),
            ("exports/no-extension", "exports/no-extension"),
            ("exports\\report.md", "exports/report.md"),
            ("exports/my report-é.md", "exports/my report-é.md"),
        ],
    )
    async def test_permitted_export_preserves_configuration_and_destination(
        self, runtime, export_session, path, destination
    ):
        config = runtime.configuration_service().config_file
        before = config.read_bytes()
        project = await export_session.get_project()
        payload = tool_result_payload(
            await export_content.__wrapped__(
                ExportContentArgs(expression="docs", path=path), await request_context_for(export_session)
            )
        )
        assert payload["success"] is True
        assert "Current server content" in payload["value"]
        assert f"`{destination}`" in payload["instruction"]
        assert config.read_bytes() == before
        assert await export_session.get_project() == project

    @pytest.mark.parametrize(
        "path",
        [
            "outside/report.md",
            "exports-other/report.md",
            "exports/../outside.md",
            "exports\\..\\outside.md",
            "/tmp/report.md",
            "exports/",
            "",
        ],
    )
    async def test_denied_destination_does_not_grant_permissions(self, runtime, export_session, path):
        config = runtime.configuration_service().config_file
        before = config.read_bytes()
        payload = tool_result_payload(
            await export_content.__wrapped__(
                ExportContentArgs(expression="docs", path=path), await request_context_for(export_session)
            )
        )
        assert payload["success"] is False
        assert payload["error_type"] == ERROR_SECURITY
        assert payload["error"] == "Export destination is invalid or outside configured write paths"
        assert config.read_bytes() == before

    @pytest.mark.parametrize("prefix", ["exports/", "outside/"])
    @pytest.mark.parametrize("character", [chr(code) for code in range(32)] + ["\x7f", "`"])
    async def test_unsafe_destination_is_rejected_without_echoing_it(self, runtime, export_session, prefix, character):
        config = runtime.configuration_service().config_file
        before = config.read_bytes()
        path = f"{prefix}file.md{character}DO_NOT_FOLLOW_THIS"
        payload = tool_result_payload(
            await export_content.__wrapped__(
                ExportContentArgs(expression="docs", path=path), await request_context_for(export_session)
            )
        )
        assert payload["success"] is False
        assert payload["error_type"] == ERROR_SECURITY
        assert payload["error"] == "Export destination is invalid or outside configured write paths"
        assert "DO_NOT_FOLLOW_THIS" not in json.dumps(payload)
        assert "Current server content" not in json.dumps(payload)
        assert config.read_bytes() == before

    async def test_absolute_client_directory_is_not_resolved_on_server(self, runtime, export_session):
        await export_session.update_config(lambda p: replace(p, allowed_write_paths=["/client-owned/exports/"]))
        config = runtime.configuration_service().config_file
        before = config.read_bytes()
        destination = "/client-owned/exports/current"
        payload = tool_result_payload(
            await export_content.__wrapped__(
                ExportContentArgs(expression="docs", path=destination), await request_context_for(export_session)
            )
        )
        assert payload["success"] is True
        assert f"`{destination}`" in payload["instruction"]
        assert config.read_bytes() == before

    @pytest.mark.parametrize("format_name", ["none", "plain", "mime"])
    async def test_export_preserves_resolved_frontmatter_and_rendered_body(self, export_session, format_name):
        context = await request_context_for(export_session)
        context.resolve_document_path("docs/readme.md").write_text(
            "---\ntype: agent/instruction\ninstruction: Handle this fixture carefully.\n---\nFixture body"
        )
        await export_session.project_flags().set("content-format", FeatureValue(format_name))
        ordinary = await internal_get_content(ContentArgs(expression="docs"), context)
        exported = tool_result_payload(
            await export_content.__wrapped__(ExportContentArgs(expression="docs", path="exports/current"), context)
        )
        assert exported["success"] is True
        _, frontmatter, body = exported["value"].split("---\n", 2)
        assert yaml.safe_load(frontmatter) == {
            "type": "agent/instruction",
            "instruction": "Handle this fixture carefully.",
        }
        assert body == ordinary.value
        assert "Fixture body" in body

    @pytest.mark.parametrize(
        "second_type,second_instruction,expected_type,expected_instruction",
        [
            ("agent/information", "Shared instruction", "agent/information", "Shared instruction"),
            ("agent/instruction", "^Priority instruction", "agent/instruction", "Priority instruction"),
        ],
    )
    async def test_multiple_document_export_uses_existing_metadata_resolution(
        self, export_session, second_type, second_instruction, expected_type, expected_instruction
    ):
        context = await request_context_for(export_session)
        context.resolve_document_path("docs/readme.md").write_text(
            "---\ntype: user/information\ninstruction: Shared instruction\n---\nFirst body"
        )
        context.resolve_document_path("docs/second.md").write_text(
            yaml.safe_dump({"type": second_type, "instruction": second_instruction}).join(["---\n", "---\nSecond body"])
        )
        exported = tool_result_payload(
            await export_content.__wrapped__(ExportContentArgs(expression="docs", path="exports/current"), context)
        )
        assert exported["success"] is True
        _, frontmatter, body = exported["value"].split("---\n", 2)
        assert yaml.safe_load(frontmatter) == {"type": expected_type, "instruction": expected_instruction}
        assert "First body" in body and "Second body" in body
        assert (await export_session.get_project()).allowed_write_paths == ["exports/", "single"]

    @pytest.mark.parametrize("route", ["tool", "uri", "native_uri"])
    async def test_prior_export_cannot_replace_content_retrieval(self, runtime, export_session, route):
        await export_content.__wrapped__(
            ExportContentArgs(expression="docs", path="exports/report.md"), await request_context_for(export_session)
        )
        context = await request_context_for(export_session)
        if route == "tool":
            result = await internal_get_content(ContentArgs(expression="docs"), context)
        elif route == "uri":
            result = await internal_read_resource(ReadResourceArgs(uri="guide://docs"), context)
        else:
            native = await guide_resource.__wrapped__("docs", "", request_context=context, request_uri=None)
            payload = json.loads(native.contents[0].content)
            assert payload["success"] is True
            assert "Current server content" in payload["value"]
            return
        assert result.success is True
        assert "Current server content" in result.value

    @pytest.mark.parametrize(
        "legacy_exports", [{"docs:": {"path": "exports/old.md", "metadata_hash": "old"}}, "obsolete"]
    )
    async def test_legacy_exports_are_ignored_without_a_migration_write(self, runtime, export_session, legacy_exports):
        config = runtime.configuration_service().config_file
        data = yaml.safe_load(config.read_text())
        key = (await export_session.get_project()).key
        data["projects"][key]["exports"] = legacy_exports
        config.write_text(yaml.safe_dump(data))
        before = config.read_bytes()
        reloaded = await bind_isolated_test_session(runtime, project_name="stateless-export")
        result = await internal_get_content(ContentArgs(expression="docs"), await request_context_for(reloaded))
        assert result.success is True
        assert "Current server content" in result.value
        assert config.read_bytes() == before
        await reloaded.update_config(lambda p: replace(p, allowed_write_paths=["exports/", "single", "other/"]))
        saved = yaml.safe_load(config.read_text())["projects"][key]
        assert "exports" not in saved
        assert saved["allowed_write_paths"] == ["exports/", "single", "other/"]

    @pytest.mark.parametrize("scopes", [frozenset(), frozenset({AuthScope.ADMIN})])
    async def test_public_mcp_export_is_unprotected_but_path_policy_still_applies(
        self, runtime, export_session, scopes
    ):
        server = FastMCP("stateless-export-boundary", lifespan=lambda _server: runtime.lifespan())
        register_tools(server)
        runtime.auth_service = AuthService(lambda: pytest.fail("Export must not invoke the provider directly"))
        with bind_user_authorisation(UserAuthorisation(scopes=scopes)):
            async with Client(FastMCPTransport(server), mode="legacy") as client:
                bound = await call_mcp_tool(
                    client, "set_project", SetCurrentProjectArgs(path=str(export_session.bound_root_path))
                )
                session_id = tool_result_payload(bound)["session_id"]
                config = runtime.configuration_service().config_file
                before = config.read_bytes()
                permitted = await call_mcp_tool(
                    client,
                    "export_content",
                    ExportContentArgs(expression="docs", path="exports/current", session_id=session_id),
                )
                assert tool_result_payload(permitted)["success"] is True
                denied = await call_mcp_tool(
                    client,
                    "export_content",
                    ExportContentArgs(expression="docs", path="outside/current", session_id=session_id),
                )
                assert tool_result_payload(denied)["success"] is False
                assert tool_result_payload(denied)["error_type"] == ERROR_SECURITY
                assert config.read_bytes() == before

    async def test_repeated_exports_return_current_payload_for_each_client_destination(self, runtime, export_session):
        config = runtime.configuration_service().config_file
        before = config.read_bytes()
        source = (await request_context_for(export_session)).resolve_document_path("docs/readme.md")
        for destination, body in [("exports/first", "First payload"), ("exports/second", "Second payload")]:
            source.write_text(body)
            response = await export_content.__wrapped__(
                ExportContentArgs(expression="docs", path=destination), await request_context_for(export_session)
            )
            payload = tool_result_payload(response)
            assert payload["success"] is True
            assert payload["value"].endswith(body)
            assert f"`{destination}`" in payload["instruction"]
        assert config.read_bytes() == before
