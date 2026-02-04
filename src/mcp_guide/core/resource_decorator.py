"""Deferred resource registration infrastructure."""

from dataclasses import dataclass
from typing import Any, Callable, Optional

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
        resource_name = func.__name__

        metadata = ResourceMetadata(name=resource_name, uri_template=uri_template, func=func, description=description)
        _RESOURCE_REGISTRY[resource_name] = ResourceRegistration(metadata=metadata)
        logger.trace(f"Resource {resource_name} added to registry (not yet registered)")

        return func

    return decorator


def register_resources(mcp: Any) -> None:
    """Register all resources with MCP server (idempotent).

    Args:
        mcp: FastMCP instance
    """
    for resource_name, registration in _RESOURCE_REGISTRY.items():
        if not registration.registered:
            mcp.resource(registration.metadata.uri_template)(registration.metadata.func)
            registration.registered = True
            logger.debug(f"Registered resource: {resource_name}")
        else:
            logger.trace(f"Resource {resource_name} already registered, skipping")


def get_resource_registry() -> dict[str, ResourceRegistration]:
    """Get a copy of the resource registry.

    Returns:
        Frozen copy of resource registry for introspection
    """
    from copy import deepcopy

    return deepcopy(_RESOURCE_REGISTRY)
