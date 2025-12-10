"""Feature flags management tools."""

from typing import Any, Optional, Union

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_guide.feature_flags.resolution import resolve_flag
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.feature_flags.validation import validate_flag_name, validate_flag_value
from mcp_guide.server import tools
from mcp_guide.tools.tool_constants import (
    ERROR_NO_PROJECT,
    INSTRUCTION_DISPLAY_ONLY,
    INSTRUCTION_NO_PROJECT,
    INSTRUCTION_VALIDATION_ERROR,
)

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


class ListFlagsArgs(ToolArguments):
    """Arguments for list_flags tool."""

    feature_name: Optional[str] = Field(None, description="Specific flag name to retrieve")
    active: bool = Field(True, description="Include resolved flags (True) or project-only (False)")


class SetFlagArgs(ToolArguments):
    """Arguments for set_flag tool."""

    feature_name: str = Field(..., description="Flag name to set")
    value: Optional[FeatureValue] = Field(True, description="Flag value to set (True=default, None=remove)")


class GetFlagArgs(ToolArguments):
    """Arguments for get_flag tool."""

    feature_name: str = Field(..., description="Flag name to retrieve")


@tools.tool(ListFlagsArgs)
async def list_flags(args: ListFlagsArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """List feature flags based on project context and parameters."""
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT).to_json_str()

    try:
        if args.active:
            # Merged flags (global + project with project precedence)
            global_proxy = session.feature_flags()
            project_proxy = session.project_flags()
            global_flags = await global_proxy.list()
            project_flags = await project_proxy.list()
            flags = {**global_flags, **project_flags}  # project overrides global
        else:
            # Project flags only
            flags_proxy = session.project_flags()
            flags = await flags_proxy.list()

        if args.feature_name:
            # Return single flag value
            return Result.ok(flags.get(args.feature_name)).to_json_str()
        else:
            # Return all flags
            return Result.ok(flags).to_json_str()

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error").to_json_str()

    except Exception as e:
        return Result.failure(
            f"Failed to list flags: {e}",
            error_type="unexpected_error",
            instruction=INSTRUCTION_DISPLAY_ONLY,
        ).to_json_str()


@tools.tool(SetFlagArgs)
async def set_flag(args: SetFlagArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Set or remove a feature flag."""
    # Validate flag name
    if not validate_flag_name(args.feature_name):
        return Result.failure(
            f"Invalid flag name '{args.feature_name}'. Flag names must contain only alphanumeric characters, hyphens, and underscores (no periods).",
            error_type="validation_error",
            instruction=INSTRUCTION_VALIDATION_ERROR,
        ).to_json_str()

    # Validate flag value if not None (removal)
    if args.value is not None and not validate_flag_value(args.value):
        return Result.failure(
            f"Invalid flag value type. Must be bool, str, list[str], or dict[str, str].",
            error_type="validation_error",
            instruction=INSTRUCTION_VALIDATION_ERROR,
        ).to_json_str()

    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT).to_json_str()

    try:
        if args.value is None:
            # Remove flag
            flags_proxy = session.project_flags()
            await flags_proxy.remove(args.feature_name)
            return Result.ok(f"Flag '{args.feature_name}' removed").to_json_str()
        else:
            # Set flag
            flags_proxy = session.project_flags()
            await flags_proxy.set(args.feature_name, args.value)
            return Result.ok(f"Flag '{args.feature_name}' set to {repr(args.value)}").to_json_str()

    except OSError as e:
        return Result.failure(f"Failed to save configuration: {e}", error_type="config_write_error").to_json_str()

    except Exception as e:
        return Result.failure(
            f"Failed to set flag: {e}", error_type="unexpected_error", instruction=INSTRUCTION_DISPLAY_ONLY
        ).to_json_str()


@tools.tool(GetFlagArgs)
async def get_flag(args: GetFlagArgs, ctx: Optional[Context] = None) -> str:  # type: ignore[type-arg]
    """Get a feature flag value with resolution hierarchy."""
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT, instruction=INSTRUCTION_NO_PROJECT).to_json_str()

    try:
        # Use resolution hierarchy: project → global → None
        project_proxy = session.project_flags()
        global_proxy = session.feature_flags()
        project_flags = await project_proxy.list()
        global_flags = await global_proxy.list()
        value = resolve_flag(args.feature_name, project_flags, global_flags)

        return Result.ok(value).to_json_str()

    except OSError as e:
        return Result.failure(f"Failed to read configuration: {e}", error_type="config_read_error").to_json_str()

    except Exception as e:
        return Result.failure(
            f"Failed to get flag: {e}", error_type="unexpected_error", instruction=INSTRUCTION_DISPLAY_ONLY
        ).to_json_str()
