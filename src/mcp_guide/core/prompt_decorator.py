"""Deferred prompt registration infrastructure."""

import json
import os
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional

from fastmcp import Context
from fastmcp.prompts import Message, PromptResult

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
_REGISTERED_PROMPT_SERVERS: set[int] = set()


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
        prompt_description = description or func.__doc__

        @wraps(func)
        async def wrapped(*args: Any, **kwargs: Any) -> object:
            result = await func(*args, **kwargs)
            ctx = kwargs.get("ctx")
            if ctx is None:
                ctx = next((arg for arg in reversed(args) if isinstance(arg, Context)), None)

            from mcp_guide.result import Result

            if isinstance(result, Result):
                from mcp_guide.tools.tool_result import prompt_result

                result = await prompt_result(prompt_name, result)
            if isinstance(result, PromptResult) and not isinstance(ctx, Context):
                return _extract_prompt_result_json(result)

            if not isinstance(ctx, Context):
                if isinstance(result, str):
                    return result
                return json.dumps({"success": False, "error": "Unsupported prompt result shape"})
            return result

        metadata = PromptMetadata(name=prompt_name, func=wrapped, description=prompt_description)
        _PROMPT_REGISTRY[prompt_name] = PromptRegistration(metadata=metadata)
        logger.trace(f"Prompt {prompt_name} added to registry (not yet registered)")

        return wrapped

    return decorator


def register_prompts(mcp: Any) -> None:
    """Register all prompts with MCP server (idempotent).

    Args:
        mcp: FastMCP instance
    """
    server_id = id(mcp)
    if server_id not in _REGISTERED_PROMPT_SERVERS:
        for prompt_name, registration in _PROMPT_REGISTRY.items():
            registered_name = get_prompt_name(prompt_name) if prompt_name == "guide" else prompt_name
            mcp.prompt(name=registered_name)(registration.metadata.func)
            registration.registered = True
            logger.debug(f"Registered prompt: {registered_name}")
        _REGISTERED_PROMPT_SERVERS.add(server_id)
    else:
        logger.trace("Prompts already registered for this server, skipping")


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


def _extract_prompt_result_json(result: PromptResult) -> str:
    """Convert a native FastMCP prompt result into JSON text."""
    messages = getattr(result, "messages", None)
    if not messages:
        return json.dumps({"success": False, "error": "Unsupported prompt result shape"})
    if isinstance(messages, str):
        return messages

    first_message = messages[0]
    if isinstance(first_message, Message):
        content = getattr(first_message, "content", None)
        if isinstance(content, list):
            if content and hasattr(content[0], "text"):
                text_value = content[0].text
                if isinstance(text_value, str):
                    return text_value
        if hasattr(content, "text") and isinstance(getattr(content, "text"), str):
            return content.text
        if isinstance(content, str):
            return content

    return json.dumps({"success": False, "error": "Unsupported prompt result shape"})
