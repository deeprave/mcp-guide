"""Deferred resource registration infrastructure."""

import weakref
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional

from fastmcp import Context
from fastmcp.resources import ResourceResult

from mcp_guide.core.mcp_log import get_logger

logger = get_logger(__name__)


@dataclass
class ResourceMetadata:
    """Metadata for a resource function."""

    name: str
    uri_template: str
    func: Callable[..., Any]
    description: Optional[str]


@dataclass
class ResourceRegistration:
    """Registration tracking for a resource."""

    metadata: ResourceMetadata
    registered: bool = False


_RESOURCE_REGISTRY: dict[str, ResourceRegistration] = {}
_REGISTERED_RESOURCE_SERVERS: dict[int, weakref.ReferenceType[Any]] = {}


def resourcefunc(
    uri_template: str, description: Optional[str] = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for deferred resource registration.

    Args:
        uri_template: URI template pattern
        description: Resource description

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        resource_name = func.__name__  # ty: ignore[unresolved-attribute]

        @wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> object:
            ctx = kwargs.get("ctx")
            if ctx is None:
                ctx = next((arg for arg in reversed(args) if isinstance(arg, Context)), None)

            from mcp_guide.session import request_session_scope

            async with request_session_scope(ctx, kwargs.get("session_id")):
                result = await func(*args, **kwargs)

            from mcp_guide.result import Result

            if isinstance(result, Result):
                from mcp_guide.mcp_result_adapter import resource_response

                return resource_response(result)

            if isinstance(result, ResourceResult) and not isinstance(ctx, Context):
                # Direct Python callers (not FastMCP resource dispatch) have
                # historically received the JSON text.  Keep that unit-test
                # and compatibility surface while preserving ResourceResult
                # for the actual SDK boundary.
                return result.contents[0].content

            return result

        metadata = ResourceMetadata(
            name=resource_name, uri_template=uri_template, func=wrapped, description=description
        )
        _RESOURCE_REGISTRY[resource_name] = ResourceRegistration(metadata=metadata)
        logger.trace(f"Resource {resource_name} added to registry (not yet registered)")

        return wrapped

    return decorator


def register_resources(mcp: Any) -> None:
    """Register all resources with MCP server (idempotent).

    Args:
        mcp: FastMCP instance
    """
    server_id = id(mcp)
    registered_server = _REGISTERED_RESOURCE_SERVERS.get(server_id)
    if registered_server is not None and registered_server() is mcp:
        logger.trace("Resources already registered for this server, skipping")
        return
    for resource_name, registration in _RESOURCE_REGISTRY.items():
        mcp.resource(registration.metadata.uri_template)(registration.metadata.func)
        registration.registered = True
        logger.debug(f"Registered resource: {resource_name}")

    def remove_released_server(reference: weakref.ReferenceType[Any]) -> None:
        if _REGISTERED_RESOURCE_SERVERS.get(server_id) is reference:
            _REGISTERED_RESOURCE_SERVERS.pop(server_id, None)

    _REGISTERED_RESOURCE_SERVERS[server_id] = weakref.ref(mcp, remove_released_server)


def get_resource_registry() -> dict[str, ResourceRegistration]:
    """Get a copy of the resource registry.

    Returns:
        Frozen copy of resource registry for introspection
    """
    from copy import deepcopy

    return deepcopy(_RESOURCE_REGISTRY)


def clear_resource_registry() -> None:
    """Clear all resources from the registry.

    Used primarily for testing to reset registration state.
    """
    _RESOURCE_REGISTRY.clear()
    _REGISTERED_RESOURCE_SERVERS.clear()
