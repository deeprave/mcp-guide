"""Deferred prompt registration infrastructure."""

import inspect
import os
import weakref
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, cast

from fastmcp import Context

from mcp_guide.core.mcp_log import get_logger

logger = get_logger(__name__)


@dataclass
class PromptMetadata:
    """Metadata for a prompt function."""

    name: str
    func: Callable[..., Any]
    description: Optional[str]


@dataclass
class PromptRegistration:
    """Registration tracking for a prompt."""

    metadata: PromptMetadata
    registered: bool = False


_PROMPT_REGISTRY: dict[str, PromptRegistration] = {}
_REGISTERED_PROMPT_SERVERS: dict[int, weakref.ReferenceType[Any]] = {}


def _transport_signature(func: Callable[..., Any]) -> inspect.Signature:
    """Keep the application context out of the client-visible prompt schema."""
    parameters = [
        parameter for parameter in inspect.signature(func).parameters.values() if parameter.name != "request_context"
    ]
    parameters.append(inspect.Parameter("ctx", inspect.Parameter.KEYWORD_ONLY, annotation=Context, default=None))
    return inspect.signature(func).replace(parameters=parameters)


def get_prompt_name(default: str = "guide") -> str:
    """Return the effective MCP prompt name."""
    return os.getenv("MCP_PROMPT_NAME", default)


def promptfunc(description: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for deferred prompt registration.

    Args:
        description: Prompt description

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        prompt_name = func.__name__  # ty: ignore[unresolved-attribute]
        prompt_description = description or inspect.cleandoc(func.__doc__ or "") or None

        @wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> object:
            ctx = kwargs.get("ctx")
            if ctx is None:
                ctx = next((arg for arg in reversed(args) if isinstance(arg, Context)), None)

            from mcp_guide.session import InvalidGuideSessionError, request_context_scope

            if ctx is None:
                raise RuntimeError("A prompt invocation requires a FastMCP context")
            application_kwargs = dict(kwargs)
            application_kwargs.pop("ctx", None)
            try:
                async with request_context_scope(
                    ctx, application_kwargs.get("session_id"), allow_pwd_bootstrap=True
                ) as request_context:
                    result = await func(*args, request_context=request_context, **application_kwargs)
                    from mcp_guide.result import Result

                    if isinstance(result, Result):
                        from mcp_guide.tools.tool_result import prompt_result

                        result = await prompt_result(
                            prompt_name,
                            result,
                            session=request_context.session,
                            session_id=request_context.session_id,
                        )
                return result
            except InvalidGuideSessionError:
                from mcp_guide.mcp_result_adapter import prompt_response
                from mcp_guide.result_constants import make_invalid_session_result

                return prompt_response(make_invalid_session_result())

        metadata = PromptMetadata(name=prompt_name, func=wrapped, description=prompt_description)
        _PROMPT_REGISTRY[prompt_name] = PromptRegistration(metadata=metadata)
        cast(Any, wrapped).__signature__ = _transport_signature(func)
        cast(Any, wrapped).__annotations__ = {**getattr(func, "__annotations__", {}), "ctx": Context}
        logger.trace(f"Prompt {prompt_name} added to registry (not yet registered)")

        return wrapped

    return decorator


def register_prompts(mcp: Any) -> None:
    """Register all prompts with MCP server (idempotent).

    Args:
        mcp: FastMCP instance
    """
    server_id = id(mcp)
    registered_server = _REGISTERED_PROMPT_SERVERS.get(server_id)
    if registered_server is not None and registered_server() is mcp:
        logger.trace("Prompts already registered for this server, skipping")
        return
    for prompt_name, registration in _PROMPT_REGISTRY.items():
        registered_name = get_prompt_name(prompt_name) if prompt_name == "guide" else prompt_name
        mcp.prompt(name=registered_name)(registration.metadata.func)
        registration.registered = True
        logger.debug(f"Registered prompt: {registered_name}")

    def remove_released_server(reference: weakref.ReferenceType[Any]) -> None:
        if _REGISTERED_PROMPT_SERVERS.get(server_id) is reference:
            _REGISTERED_PROMPT_SERVERS.pop(server_id, None)

    _REGISTERED_PROMPT_SERVERS[server_id] = weakref.ref(mcp, remove_released_server)


def get_prompt_registry() -> dict[str, PromptRegistration]:
    """Get a copy of the prompt registry.

    Returns:
        Frozen copy of prompt registry for introspection
    """
    from copy import deepcopy

    return deepcopy(_PROMPT_REGISTRY)


def clear_prompt_registry() -> None:
    """Clear all prompts from the registry.

    Used primarily for testing to reset registration state.
    """
    _PROMPT_REGISTRY.clear()
    _REGISTERED_PROMPT_SERVERS.clear()
