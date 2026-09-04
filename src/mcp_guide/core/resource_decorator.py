"""Deferred resource registration infrastructure."""

import inspect
import weakref
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, cast

from fastmcp import Context

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.mcp_context import resource_uri_from_fastmcp

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


def _transport_signature(func: Callable[..., Any]) -> inspect.Signature:
    """Expose resource URI parameters and FastMCP context, not application inputs."""
    parameters = []
    for parameter in inspect.signature(func).parameters.values():
        if parameter.name in {"request_context", "request_uri"}:
            continue
        parameters.append(parameter)
    parameters.append(inspect.Parameter("ctx", inspect.Parameter.KEYWORD_ONLY, annotation=Context, default=None))
    return inspect.signature(func).replace(parameters=parameters)


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

            from mcp_guide.session import InvalidGuideSessionError, request_context_scope

            if ctx is None:
                raise RuntimeError("A resource invocation requires a FastMCP context")
            application_kwargs = dict(kwargs)
            application_kwargs.pop("ctx", None)
            try:
                async with request_context_scope(
                    ctx, application_kwargs.get("session_id"), allow_pwd_bootstrap=True
                ) as request_context:
                    result = await func(
                        *args,
                        request_context=request_context,
                        request_uri=resource_uri_from_fastmcp(ctx),
                        **application_kwargs,
                    )
            except InvalidGuideSessionError:
                from mcp_guide.mcp_result_adapter import resource_response
                from mcp_guide.result_constants import make_invalid_session_result

                return resource_response(make_invalid_session_result())

            from mcp_guide.result import Result

            if isinstance(result, Result):
                from mcp_guide.mcp_result_adapter import resource_response

                return resource_response(result)

            return result

        advertised_description = description or inspect.cleandoc(func.__doc__ or "") or None
        metadata = ResourceMetadata(
            name=resource_name,
            uri_template=uri_template,
            func=wrapped,
            description=advertised_description,
        )
        _RESOURCE_REGISTRY[resource_name] = ResourceRegistration(metadata=metadata)
        cast(Any, wrapped).__signature__ = _transport_signature(func)
        cast(Any, wrapped).__annotations__ = {**getattr(func, "__annotations__", {}), "ctx": Context}
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
