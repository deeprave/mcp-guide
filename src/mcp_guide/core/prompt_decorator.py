"""Deferred prompt registration infrastructure."""

from dataclasses import dataclass
from typing import Any, Callable, Optional

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


def promptfunc(description: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for deferred prompt registration.

    Args:
        description: Prompt description

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        prompt_name = func.__name__

        metadata = PromptMetadata(name=prompt_name, func=func, description=description)
        _PROMPT_REGISTRY[prompt_name] = PromptRegistration(metadata=metadata)
        logger.trace(f"Prompt {prompt_name} added to registry (not yet registered)")

        return func

    return decorator


def register_prompts(mcp: Any) -> None:
    """Register all prompts with MCP server (idempotent).

    Args:
        mcp: FastMCP instance
    """
    for prompt_name, registration in _PROMPT_REGISTRY.items():
        if not registration.registered:
            mcp.prompt()(registration.metadata.func)
            registration.registered = True
            logger.debug(f"Registered prompt: {prompt_name}")
        else:
            logger.trace(f"Prompt {prompt_name} already registered, skipping")


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
