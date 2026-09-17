"""MCP resource handlers for guide:// URI scheme."""

from typing import Annotated, Any, Optional

from fastmcp import Context
from pydantic import Field

from mcp_guide.core.arguments import SESSION_ID_DESCRIPTION
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.resource_decorator import resourcefunc
from mcp_guide.mcp_result_adapter import resource_response
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_INVALID_NAME
from mcp_guide.runtime import RequestContext
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content
from mcp_guide.tools.tool_resource import ReadResourceArgs, internal_read_resource
from mcp_guide.validation import InvalidProjectNameError

logger = get_logger(__name__)


async def _process_and_serialize(result: Result[Any], request_context: RequestContext) -> object:
    """Run a Result through the already-resolved Session and adapt it once."""
    try:
        result = await request_context.process_result(result)
    except Exception as e:
        logger.error(f"TaskManager processing failed for resource: {e}")
    return resource_response(
        result,
        session_id=request_context.session_id,
        protocol_type=request_context.session.protocol_type,
    )


async def _resolve_guide_uri(
    uri: str, request_context: RequestContext, *, mcp_context: Context | None = None
) -> object:
    """Resolve a guide:// URI through the shared read_resource implementation."""
    result = await internal_read_resource(
        ReadResourceArgs(uri=uri, session_id=request_context.session_id), request_context, mcp_context=mcp_context
    )
    if not isinstance(result, Result):
        return result
    return await _process_and_serialize(result, request_context)


@resourcefunc("guide://${?session_id,verbose,table}")
async def guide_skills_catalog(
    session_id: Annotated[Optional[str], Field(description=SESSION_ID_DESCRIPTION)] = None,
    verbose: Annotated[bool, Field(description="Return the user-facing skills catalogue.")] = False,
    table: Annotated[bool, Field(description="Return the user-facing skills catalogue as a Markdown table.")] = False,
    *,
    request_context: RequestContext,
    request_uri: str | None,
    mcp_context: Context | None = None,
) -> object:
    """List Guide-provided skills as individual entrypoints.

    Each item is derived from the skill's frontmatter and supplies a stable identifier,
    purpose, and URI for explicitly retrieving its complete instructions.
    """
    try:
        uri = request_uri or (
            "guide://$?verbose=true&table=true"
            if verbose and table
            else "guide://$?table=true"
            if table
            else "guide://$?verbose=true"
            if verbose
            else "guide://$"
        )
        return await _resolve_guide_uri(uri, request_context)
    except (ValueError, FileNotFoundError, PermissionError) as error:
        return resource_response(Result.failure(str(error)))
    except Exception as error:
        logger.error("Unexpected error listing Guide skills: %s", error, exc_info=True)
        return resource_response(Result.failure(f"Unexpected error: {error}"))


@resourcefunc("guide://${skill_path*}{?session_id}")
async def guide_skill_resource(
    skill_path: Annotated[
        str,
        Field(description="Slash-separated skill path after the dollar prefix, advertised by guide://$."),
    ],
    session_id: Annotated[Optional[str], Field(description=SESSION_ID_DESCRIPTION)] = None,
    *,
    request_context: RequestContext,
    request_uri: str | None,
    mcp_context: Context | None = None,
) -> object:
    """Retrieve a package member from an explicitly selected Guide skill.

    ``guide://$workflow-status`` resolves to
    ``{docroot}/_skills/workflow-status/SKILL.md``. A suffix such as
    ``/resources/checklist.md`` resolves a named member below the same package
    root, using the normal template suffix handling used for Guide commands.
    """
    try:
        uri = request_uri or f"guide://${skill_path}"
        return await _resolve_guide_uri(uri, request_context, mcp_context=mcp_context)
    except (ValueError, FileNotFoundError, PermissionError) as error:
        return resource_response(Result.failure(str(error)))
    except Exception as error:
        logger.error("Unexpected error reading Guide skill %s: %s", skill_path, error, exc_info=True)
        return resource_response(Result.failure(f"Unexpected error: {error}"))


@resourcefunc("guide://{collection}/{document}{?session_id}")
async def guide_resource(
    collection: Annotated[
        str,
        Field(
            description=(
                "Collection or category name. A name starting with _ is a command URI and a name "
                "starting with $ is a skill URI."
            )
        ),
    ],
    document: Annotated[
        str,
        Field(
            description="Optional document pattern or sub-path filter. Empty means the whole collection or category."
        ),
    ] = "",
    session_id: Annotated[Optional[str], Field(description=SESSION_ID_DESCRIPTION)] = None,
    *,
    request_context: RequestContext,
    request_uri: str | None,
    mcp_context: Context | None = None,
) -> object:
    """Read Guide content for a collection or category.

    collection is the collection or category name; document is an optional pattern.
    Pass session_id from set_project as the URI query parameter. Command URIs use the
    guide://_ template instead. Skill URIs use the guide://$ template.
    """
    try:
        if collection.startswith("_"):
            uri = request_uri or f"guide://{collection}"
            if document and request_uri is None:
                uri = f"{uri}/{document}"
            return await _resolve_guide_uri(uri, request_context, mcp_context=mcp_context)
        if collection.startswith("$"):
            uri = request_uri or f"guide://{collection}"
            if document and request_uri is None:
                uri = f"{uri}/{document}"
            return await _resolve_guide_uri(uri, request_context, mcp_context=mcp_context)

        # For guide://policies/<topic>, append a trailing slash to the document so that
        # gather_category_fileinfos treats it as a sub-path filter against the project's
        # configured patterns rather than a direct pattern override.
        pattern: str | None
        if collection == "policies" and document:
            pattern = document + "/"
        else:
            pattern = document if document else None

        content_args = ContentArgs(
            expression=collection, pattern=pattern, force=False, session_id=request_context.session_id
        )
        result = await internal_get_content(content_args, request_context)
        return await _process_and_serialize(result, request_context)

    except InvalidProjectNameError as error:
        return resource_response(Result.failure(str(error), error_type=ERROR_INVALID_NAME))
    except (ValueError, FileNotFoundError, PermissionError) as e:
        return resource_response(Result.failure(str(e)))
    except Exception as e:
        # Log unexpected exceptions for debugging while still handling them
        logger.error(f"Unexpected error in guide_resource: {type(e).__name__}: {str(e)}", exc_info=True)
        return resource_response(Result.failure(f"Unexpected error: {str(e)}"))


@resourcefunc("guide://_{command_path*}{?session_id}")
async def guide_command_resource(
    command_path: Annotated[
        str,
        Field(description="Command path after the underscore, including slash-separated argv segments."),
    ],
    session_id: Annotated[Optional[str], Field(description=SESSION_ID_DESCRIPTION)] = None,
    *,
    request_context: RequestContext,
    request_uri: str | None,
) -> object:
    """Read output from a Guide command URI (guide://_command/args).

    command_path is the command and path segments after the underscore. Pass session_id
    from set_project as the URI query parameter.
    """
    try:
        uri = request_uri or f"guide://_{command_path}"
        return await _resolve_guide_uri(uri, request_context)
    except InvalidProjectNameError as error:
        return resource_response(Result.failure(str(error), error_type=ERROR_INVALID_NAME))
    except (ValueError, FileNotFoundError, PermissionError) as e:
        return resource_response(Result.failure(str(e)))
    except Exception as e:
        logger.error(f"Unexpected error in guide_command_resource: {type(e).__name__}: {str(e)}", exc_info=True)
        return resource_response(Result.failure(f"Unexpected error: {str(e)}"))
