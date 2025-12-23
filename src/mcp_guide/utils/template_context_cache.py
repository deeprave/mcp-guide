"""Template context cache with session listener for decoupled context management."""

import logging
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from mcp_guide.utils.file_discovery import FileInfo
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

    async def _build_system_context(self) -> "TemplateContext":
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

    async def _build_agent_context(self) -> "TemplateContext":
        """Build agent context with @ symbol default and agent info if available."""
        import os

        from mcp_guide.mcp_context import cached_mcp_context
        from mcp_guide.utils.template_context import TemplateContext

        agent_vars: dict[str, Any] = {
            "@": "@"  # @ symbol always available
        }

        # Add tool_prefix from MCP_TOOL_PREFIX environment variable
        mcp_tool_prefix = os.environ.get("MCP_TOOL_PREFIX", "guide")
        if mcp_tool_prefix == "guide" or not mcp_tool_prefix:
            tool_prefix = "guide_"
        else:
            tool_prefix = f"{mcp_tool_prefix}_"
        agent_vars["tool_prefix"] = tool_prefix

        # Try to get agent information from global ContextVar
        try:
            cached_context = cached_mcp_context.get()
            if cached_context and cached_context.agent_info:
                agent_info = cached_context.agent_info
                # Resolve the prompt prefix template with actual MCP name
                resolved_prefix = agent_info.prompt_prefix.replace("{mcp_name}", "guide")
                agent_vars["@"] = resolved_prefix  # Set @ to the resolved prefix
                agent_vars["agent"] = {
                    "name": agent_info.name,
                    "class": agent_info.normalized_name,  # agent.class for canonical form
                    "version": agent_info.version or "",
                    "prefix": resolved_prefix,
                }
        except (AttributeError, KeyError, ValueError) as e:
            # Agent detection failed - log and use @ symbol only
            logger.debug(f"Agent detection failed: {e}")

        return TemplateContext(agent_vars)

    async def _build_project_context(self) -> "TemplateContext":
        """Build project context with current project data."""
        from mcp_guide.session import get_current_session
        from mcp_guide.utils.template_context import TemplateContext

        # Extract project information from current session using public API
        project_name = ""
        project_key = ""
        project_hash = ""
        project_flags = {}
        categories_list: list[dict[str, Any]] = []
        collections_list: list[dict[str, Any]] = []
        flags_list: list[dict[str, Any]] = []

        try:
            session = get_current_session()
            if session:
                project = await session.get_project()
                project_name = project.name
                project_key = project.key or project_name  # Fallback for legacy projects
                project_hash = project.hash or ""  # Fallback for legacy projects
                project_flags = project.project_flags or {}

                # Convert categories dict to list format with pre-formatted patterns
                categories_list = [
                    {
                        "name": cat_name,
                        "dir": cat.dir,
                        "patterns": cat.patterns,
                        "patterns_str": ", ".join(f"`{p}`" for p in cat.patterns) if cat.patterns else "",
                        "description": cat.description,
                    }
                    for cat_name, cat in project.categories.items()
                ]

                # Convert collections dict to list format with pre-formatted categories
                collections_list = [
                    {
                        "name": col_name,
                        "description": col.description,
                        "categories": col.categories,
                        "categories_str": ", ".join(f"`{c}`" for c in col.categories) if col.categories else "",
                    }
                    for col_name, col in project.collections.items()
                ]
        except (AttributeError, ValueError, RuntimeError) as e:
            logger.debug(f"Failed to get project from session: {e}")

        # Get global flags for template context
        global_flags_dict = {}
        global_flags_list = []
        try:
            if session:
                global_flags_dict = await session.feature_flags().list()
                global_flags_list = [{"key": k, "value": v} for k, v in global_flags_dict.items()]
        except Exception as e:
            logger.debug(f"Failed to get global flags: {e}")

        # Get projects list for template context
        projects_data: dict[str, Any] = {}
        projects_count = 0
        try:
            if session:
                from mcp_guide.session import list_all_projects

                projects_result = await list_all_projects(session, verbose=True)
                if projects_result.success and projects_result.value:
                    projects_dict = projects_result.value.get("projects", {})
                    # Convert to array format for Mustache iteration with current project marking
                    current_project = project_name
                    projects_list: list[dict[str, Any]] = []
                    for name, data in projects_dict.items():
                        # Format categories with patterns_str
                        categories = []
                        for cat in data.get("categories", []):
                            patterns = cat.get("patterns", [])
                            patterns_str = ", ".join(f"`{p}`" for p in patterns) if patterns else ""
                            categories.append({**cat, "patterns_str": patterns_str})

                        # Format collections with categories_str
                        collections = []
                        for col in data.get("collections", []):
                            col_categories = col.get("categories", [])
                            categories_str = ", ".join(f"`{c}`" for c in col_categories) if col_categories else ""
                            collections.append({**col, "categories_str": categories_str})

                        projects_list.append(
                            {
                                "key": name,
                                "value": {**data, "categories": categories, "collections": collections},
                                "current": name == current_project,
                            }
                        )
                    projects_count = len(projects_dict)
                    projects_data = {"projects": projects_list}
        except Exception as e:
            logger.debug(f"Failed to get projects list: {e}")

        project_vars = {
            "project": {
                "name": project_name,
                "key": project_key,
                "hash": project_hash,
                "project_flags": project_flags,  # Dict format for conditionals
                "project_flag_values": [
                    {"key": k, "value": v} for k, v in project_flags.items()
                ],  # List format for iteration
                "categories": categories_list,
                "collections": collections_list,
            },
            "feature_flags": global_flags_dict,  # Dict format for conditionals
            "feature_flag_values": global_flags_list,  # List format for iteration
            "projects": projects_data,
            "projects_count": projects_count,
        }

        return TemplateContext(project_vars)

    async def _build_category_context(self, category_name: str) -> "TemplateContext":
        """Build category context with category data (not cached)."""
        from mcp_guide.session import get_current_session
        from mcp_guide.utils.template_context import TemplateContext

        # Extract category information from current session's project
        category_data = {"name": "", "dir": "", "patterns": [], "description": ""}
        try:
            session = get_current_session()
            if session:
                project = await session.get_project()
                # Find category by name using dict lookup
                if category_name in project.categories:
                    category = project.categories[category_name]
                    category_data = {
                        "name": category_name,  # Inject name from dict key
                        "dir": category.dir,
                        "patterns": category.patterns,
                        "description": getattr(category, "description", ""),
                    }
        except (AttributeError, ValueError, RuntimeError) as e:
            logger.debug(f"Failed to get category from session: {e}")

        category_vars = {"category": category_data}
        return TemplateContext(category_vars)

    async def _build_collection_context(self, collection_name: str) -> "TemplateContext":
        """Build collection context with collection data (not cached)."""
        from mcp_guide.session import get_current_session
        from mcp_guide.utils.template_context import TemplateContext

        # Extract collection information from current session's project
        collection_data = {"name": "", "categories": [], "description": ""}
        try:
            session = get_current_session()
            if session:
                project = await session.get_project()
                # Find collection by name using dict lookup
                if collection_name in project.collections:
                    collection = project.collections[collection_name]
                    collection_data = {
                        "name": collection_name,  # Inject name from dict key
                        "categories": collection.categories,
                        "description": getattr(collection, "description", ""),
                    }
        except (AttributeError, ValueError, RuntimeError) as e:
            logger.debug(f"Failed to get collection from session: {e}")

        collection_vars = {"collection": collection_data}
        return TemplateContext(collection_vars)

    async def get_template_contexts(self, category_name: Optional[str] = None) -> "TemplateContext":
        """Get layered template contexts for rendering.

        Args:
            category_name: Optional category name for category-specific context

        Returns:
            TemplateContext with layered contexts (system → agent → project → category)
        """

        # Check cache first (only for non-category contexts)
        if category_name is None:
            cached = _template_contexts.get()
            if cached is not None:
                return cached

        # Build contexts
        system_context = await self._build_system_context()
        agent_context = await self._build_agent_context()
        project_context = await self._build_project_context()

        # Create layered context: project context with agent and system as parents
        layered_context = project_context.new_child(agent_context.new_child(system_context))

        # Add category context if requested (not cached)
        if category_name is not None:
            category_context = await self._build_category_context(category_name)
            layered_context = category_context.new_child(layered_context)
        else:
            # Cache only when no category context (base contexts only)
            _template_contexts.set(layered_context)

        return layered_context

    def get_transient_context(self) -> "TemplateContext":
        """Generate fresh transient context with timestamps.

        Returns:
            TemplateContext with fresh timestamp data
        """
        import time
        from datetime import datetime, timezone

        from mcp_guide.utils.template_context import TemplateContext

        # Get single high-resolution timestamp
        timestamp_ns = time.time_ns()

        # Calculate all timestamp formats from the same source
        timestamp = timestamp_ns / 1_000_000_000  # seconds (float)
        timestamp_ms = timestamp_ns / 1_000_000  # milliseconds (float)

        # Generate datetime objects
        now_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        now = datetime.fromtimestamp(timestamp).replace(
            tzinfo=datetime.now().astimezone().tzinfo
        )  # local timezone aware

        transient_vars = {
            "timestamp": timestamp,
            "timestamp_ms": timestamp_ms,
            "timestamp_ns": timestamp_ns,
            "now": {
                "date": now.strftime("%Y-%m-%d"),
                "day": now.strftime("%A"),
                "time": now.strftime("%H:%M"),
                "tz": now.strftime("%z"),
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S%z"),
            },
            "now_utc": {
                "date": now_utc.strftime("%Y-%m-%d"),
                "day": now_utc.strftime("%A"),
                "time": now_utc.strftime("%H:%M"),
                "tz": "+0000",
                "datetime": now_utc.strftime("%Y-%m-%d %H:%M:%SZ"),
            },
        }

        return TemplateContext(transient_vars)


# Global instance for use across the application
template_context_cache = TemplateContextCache()


async def get_template_context_if_needed(
    files: list["FileInfo"], category_name: Optional[str] = None
) -> Optional["TemplateContext"]:
    """Get template context only if files contain templates.

    Args:
        files: List of FileInfo objects to check
        category_name: Category name for context building

    Returns:
        TemplateContext if templates found, None otherwise
    """
    from mcp_guide.utils.template_renderer import is_template_file

    if any(is_template_file(file_info) for file_info in files):
        return await get_template_contexts(category_name)
    return None


async def get_template_contexts(category_name: Optional[str] = None) -> "TemplateContext":
    """Public API to get template contexts for rendering.

    Args:
        category_name: Optional category name for category-specific context

    Returns:
        TemplateContext with layered contexts
    """
    return await template_context_cache.get_template_contexts(category_name)
