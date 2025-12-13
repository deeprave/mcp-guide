"""Template context cache with session listener for decoupled context management."""

import logging
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from mcp_guide.utils.template_context import TemplateContext

from mcp_guide.session_listener import SessionListener

logger = logging.getLogger(__name__)

# ContextVar for thread-safe template context cache
_template_contexts: ContextVar[Optional["TemplateContext"]] = ContextVar("template_contexts", default=None)


class TemplateContextCache(SessionListener):
    """Template context cache that listens to session changes."""

    def on_session_changed(self, project_name: str) -> None:
        """Invalidate cache when session changes."""
        _template_contexts.set(None)
        logger.debug(f"Template context cache invalidated for project: {project_name}")

    def _build_system_context(self) -> "TemplateContext":
        """Build system context with static system information."""
        import platform

        from mcp_guide.utils.template_context import TemplateContext

        system_vars = {
            "system": {
                "os": platform.system(),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
            }
        }

        return TemplateContext(system_vars)

    def _build_agent_context(self) -> "TemplateContext":
        """Build agent context with @ symbol default and agent info if available."""
        from mcp_guide.mcp_context import cached_mcp_context
        from mcp_guide.utils.template_context import TemplateContext

        agent_vars: dict[str, Any] = {
            "@": "@"  # @ symbol always available
        }

        # Try to get agent information from global ContextVar
        try:
            cached_context = cached_mcp_context.get()
            if cached_context and cached_context.agent_info:
                agent_info = cached_context.agent_info
                agent_vars["agent"] = {
                    "name": agent_info.name,
                    "class": agent_info.normalized_name,  # agent.class for canonical form
                    "version": agent_info.version or "",
                    "prefix": agent_info.prompt_prefix or "",
                }
        except (AttributeError, KeyError, ValueError) as e:
            # Agent detection failed - log and use @ symbol only
            logger.debug(f"Agent detection failed: {e}")
            pass

        return TemplateContext(agent_vars)

    def get_template_contexts(self, category_name: Optional[str] = None) -> "TemplateContext":
        """Get layered template contexts for rendering.

        Args:
            category_name: Optional category name for category-specific context

        Returns:
            TemplateContext with layered contexts (system → agent → project → category)
        """

        # Check cache first
        cached = _template_contexts.get()
        if cached is not None:
            return cached

        # Build contexts
        system_context = self._build_system_context()
        agent_context = self._build_agent_context()

        # Create layered context: agent context with system as parent
        layered_context = agent_context.new_child(system_context)

        # Cache the result
        _template_contexts.set(layered_context)

        # TODO: Add project and category contexts to the chain when implemented
        return layered_context


# Global instance for use across the application
template_context_cache = TemplateContextCache()


def get_template_contexts(category_name: Optional[str] = None) -> "TemplateContext":
    """Public API to get template contexts for rendering.

    Args:
        category_name: Optional category name for category-specific context

    Returns:
        TemplateContext with layered contexts
    """
    return template_context_cache.get_template_contexts(category_name)
