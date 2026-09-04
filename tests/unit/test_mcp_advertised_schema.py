"""Advertised MCP tool, prompt, and resource schema contracts."""

import importlib
import inspect
import sys
from typing import Annotated, Any, get_args, get_origin

from mcp_guide.core.arguments import SESSION_ID_DESCRIPTION
from mcp_guide.core.prompt_decorator import get_prompt_registry
from mcp_guide.core.resource_decorator import get_resource_registry
from mcp_guide.core.tool_decorator import get_tool_registry
from mcp_guide.tools.tool_content import ContentArgs, ExportContentArgs
from mcp_guide.tools.tool_feature_flags import SetFeatureFlagArgs, SetFlagArgs
from mcp_guide.tools.tool_filesystem import SendDirectoryListingArgs, SendFileContentArgs
from mcp_guide.tools.tool_project import CloneProjectArgs, SetCurrentProjectArgs
from mcp_guide.tools.tool_utility import GetClientInfoArgs


def _reload_module(qualified_name: str) -> None:
    module = sys.modules.get(qualified_name)
    if module is not None:
        importlib.reload(module)
    else:
        importlib.import_module(qualified_name)


def _ensure_production_surface() -> None:
    """Reload decorator modules when a prior test cleared the registries."""
    if "set_project" not in get_tool_registry():
        import mcp_guide.tools  # noqa: F401

        for module_name in (
            "tool_category",
            "tool_collection",
            "tool_content",
            "tool_discovery",
            "tool_document",
            "tool_document_update",
            "tool_feature_flags",
            "tool_filesystem",
            "tool_project",
            "tool_resource",
            "tool_update",
            "tool_utility",
        ):
            _reload_module(f"mcp_guide.tools.{module_name}")
    if "guide" not in get_prompt_registry():
        _reload_module("mcp_guide.prompts.guide_prompt")
    if "guide_resource" not in get_resource_registry():
        _reload_module("mcp_guide.resources")


def _annotated_description(annotation: Any) -> str | None:
    if get_origin(annotation) is Annotated:
        for extra in get_args(annotation)[1:]:
            description = getattr(extra, "description", None)
            if description:
                return description
    return None


def test_session_id_is_guide_continuation_not_fastmcp() -> None:
    markdown = SetCurrentProjectArgs.to_schema_markdown()
    assert "FastMCP session identifier" not in markdown
    assert SESSION_ID_DESCRIPTION in markdown


def test_clone_project_advertises_bound_destination() -> None:
    from mcp_guide.tools.tool_project import clone_project

    description = CloneProjectArgs.build_description(clone_project)
    assert "from one project to another" not in description
    assert "currently bound project" in description
    assert "bypass safeguards" not in description
    assert "replace mode" in description.lower() or "merge=False" in description


def test_category_collection_list_default_is_verbose() -> None:
    from mcp_guide.tools.tool_category import CategoryCollectionListArgs, category_collection_list

    description = CategoryCollectionListArgs.build_description(category_collection_list)
    assert "names only by default" not in description
    assert "full details by default" in description


def test_set_project_does_not_say_switching() -> None:
    from mcp_guide.tools.tool_project import set_project

    description = SetCurrentProjectArgs.build_description(set_project)
    assert "after switching" not in description
    assert "after binding" in description


def test_client_info_has_no_unused_verbose_argument() -> None:
    assert "verbose" not in GetClientInfoArgs.model_fields
    from mcp_guide.tools.tool_utility import client_info

    description = GetClientInfoArgs.build_description(client_info)
    assert "Unused parameter" not in description


def test_content_expression_advertises_comma_and_slash_grammar() -> None:
    expression = ContentArgs.model_fields["expression"].description
    assert expression is not None
    assert "Comma-separated" in expression
    assert ExportContentArgs.model_fields["expression"].description == expression


def test_send_file_content_path_is_opaque() -> None:
    description = SendFileContentArgs.model_fields["path"].description
    assert description is not None
    assert "that was requested" not in description
    assert "opaque" in description.lower()


def test_send_directory_listing_path_is_validated() -> None:
    description = SendDirectoryListingArgs.model_fields["path"].description
    assert description is not None
    assert "opaque" not in description.lower()
    assert "read policy" in description.lower()


def test_flag_value_types_are_complete() -> None:
    for args_class in (SetFlagArgs, SetFeatureFlagArgs):
        description = args_class.model_fields["value"].description
        assert description is not None
        assert "list[str]" in description
        assert "True=default" not in description


def test_registered_tool_descriptions_have_no_stale_contracts() -> None:
    _ensure_production_surface()
    registry = get_tool_registry()
    assert "set_project" in registry
    forbidden = (
        "FastMCP session identifier",
        "from one project to another",
        "names only by default",
        "after switching",
        "Unused parameter for compatibility",
        "File path that was requested",
        "True=default, None=remove",
    )
    for name, registration in registry.items():
        description = registration.metadata.description or ""
        for fragment in forbidden:
            assert fragment not in description, f"{name} still advertises {fragment!r}"
        schema = registration.metadata.args_class.model_json_schema()
        session = schema["properties"]["session_id"]
        assert SESSION_ID_DESCRIPTION == session["description"]
        assert "request_context" not in description
        assert "Args:" not in description.split("## Arguments")[0]


def test_promptfunc_cleans_docstring_indentation() -> None:
    from mcp_guide.core.prompt_decorator import _PROMPT_REGISTRY, promptfunc

    @promptfunc()
    async def indented_prompt_description() -> None:
        """
        Leading indent must not be advertised.
        """

    try:
        description = _PROMPT_REGISTRY["indented_prompt_description"].metadata.description
        assert description == "Leading indent must not be advertised."
    finally:
        _PROMPT_REGISTRY.pop("indented_prompt_description", None)


def test_guide_prompt_arguments_describe_command_and_session() -> None:
    _ensure_production_surface()
    registration = get_prompt_registry()["guide"]
    description = registration.metadata.description or ""
    assert "Access Guide commands" in description
    assert "request_context" not in description
    signature = inspect.signature(registration.metadata.func)
    arg1 = _annotated_description(signature.parameters["arg1"].annotation)
    session_id = _annotated_description(signature.parameters["session_id"].annotation)
    assert arg1 is not None and ":help" in arg1
    assert session_id == SESSION_ID_DESCRIPTION


def test_resource_templates_document_session_id() -> None:
    _ensure_production_surface()
    registry = get_resource_registry()
    content = registry["guide_resource"]
    command = registry["guide_command_resource"]
    assert "request_context" not in (content.metadata.description or "")
    assert "session_id" in (content.metadata.description or "").lower()
    assert "request_context" not in (command.metadata.description or "")
    content_signature = inspect.signature(content.metadata.func)
    assert _annotated_description(content_signature.parameters["collection"].annotation)
    assert _annotated_description(content_signature.parameters["session_id"].annotation) == SESSION_ID_DESCRIPTION
