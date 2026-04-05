"""Template context cache with session listener for decoupled context management."""

import platform
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from mcp_guide.session import Session

from mcp_guide import __version__
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.files import FileInfo
from mcp_guide.feature_flags.constants import FLAG_WORKFLOW, FLAG_WORKFLOW_CONSENT, FLAG_WORKFLOW_FILE
from mcp_guide.render.context import TemplateContext
from mcp_guide.result_constants import (
    INSTRUCTION_AGENT_INFORMATION,
    INSTRUCTION_AGENT_INSTRUCTIONS,
    INSTRUCTION_AGENT_REQUIREMENTS,
    INSTRUCTION_DISPLAY_ERRORS,
    INSTRUCTION_DISPLAY_ONLY,
    INSTRUCTION_ERROR_MESSAGE,
    INSTRUCTION_NO_DISPLAY,
)
from mcp_guide.session_listener import SessionListener
from mcp_guide.workflow.constants import DEFAULT_WORKFLOW_CONSENT, DEFAULT_WORKFLOW_FILE
from mcp_guide.workflow.flags import parse_workflow_phases, substitute_variables

logger = get_logger(__name__)

HANDOFF_AGENT_CLASSES = {"codex", "q-dev", "claude"}
EXAMINED_AGENT_FLAGS = (
    "codex",
    "q_dev",
    "kiro",
    "claude",
    "cursor",
    "copilot",
    "gemini",
    "windsurf",
    "opencode",
    "unknown",
)


class TemplateContextCache(SessionListener):
    """Template context cache that listens to session changes. One instance per session."""

    def __init__(self) -> None:
        self._cache: Optional["TemplateContext"] = None

    def invalidate(self) -> None:
        """Invalidate the cached template context."""
        self._cache = None

    async def on_project_changed(self, session: "Session", old_project: str, new_project: str) -> None:
        """Invalidate cache when project switches."""
        self.invalidate()
        logger.debug(f"Template context cache invalidated: project switch {old_project} -> {new_project}")

    async def on_config_changed(self, session: "Session") -> None:
        """Invalidate cache when project configuration changes."""
        self.invalidate()
        logger.debug(f"Template context cache invalidated due to config change: {session.project_name}")

    async def _build_system_context(self) -> "TemplateContext":
        """Build system context with static system information."""
        server_vars = {
            "server": {
                "os": platform.system(),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "version": __version__,
            },
            "INSTRUCTION_DISPLAY_ONLY": INSTRUCTION_DISPLAY_ONLY,
            "INSTRUCTION_ERROR_MESSAGE": INSTRUCTION_ERROR_MESSAGE,
            "INSTRUCTION_NO_DISPLAY": INSTRUCTION_NO_DISPLAY,
            "INSTRUCTION_DISPLAY_ERRORS": INSTRUCTION_DISPLAY_ERRORS,
            "INSTRUCTION_AGENT_INFORMATION": INSTRUCTION_AGENT_INFORMATION,
            "INSTRUCTION_AGENT_INSTRUCTIONS": INSTRUCTION_AGENT_INSTRUCTIONS,
            "INSTRUCTION_AGENT_REQUIREMENTS": INSTRUCTION_AGENT_REQUIREMENTS,
        }

        return TemplateContext(server_vars)

    async def _build_client_context(self) -> "TemplateContext":
        """Build client context from cached client data."""
        # Deferred import: avoids circular dependency (tool_decorator → task_manager → render → cache → task_manager)
        from mcp_guide.task_manager import get_task_manager

        task_manager = get_task_manager()
        client_os_info = task_manager.get_cached_data("client_os_info") or {}
        client_context_info = task_manager.get_cached_data("client_context_info") or {}

        # Merge client data
        client_vars: dict[str, Any] = {"client": {}}
        if "client" in client_os_info:
            client_vars["client"].update(client_os_info["client"])
        if "user" in client_context_info:
            client_vars["user"] = client_context_info["user"]
        if "repo" in client_context_info:
            client_vars["repo"] = client_context_info["repo"]

        return TemplateContext(client_vars)

    async def _build_agent_context(self) -> "TemplateContext":
        """Build agent context with @ symbol default and agent info if available."""
        agent_vars: dict[str, Any] = {
            "@": "@"  # @ symbol always available
        }

        # Add tool_prefix from MCP_TOOL_PREFIX environment variable
        # Import here to avoid circular dependency with tool_decorator module
        from mcp_guide.core.tool_decorator import get_tool_prefix

        tool_prefix = get_tool_prefix()
        agent_vars["tool_prefix"] = tool_prefix

        # Try to get agent and styling information from session
        styling_value = "plain"
        try:
            from mcp_guide.feature_flags.constants import FLAG_CONTENT_STYLE
            from mcp_guide.models import resolve_all_flags
            from mcp_guide.session import get_active_session

            session = get_active_session()
            if session is None:
                raise RuntimeError("No active session")

            if session.agent_info:
                agent_info = session.agent_info
                resolved_prefix = (
                    agent_info.prompt_prefix.replace("{mcp_name}", "guide")
                    if agent_info.prompt_prefix is not None
                    else ""
                )
                normalized_name = agent_info.normalized_name
                normalized_flag = normalized_name.replace("-", "_")
                agent_context = {
                    "name": agent_info.name,
                    "class": normalized_name,
                    "version": agent_info.version or "",
                    "prefix": resolved_prefix,
                    "has_handoff": normalized_name in HANDOFF_AGENT_CLASSES,
                }

                for flag_name in EXAMINED_AGENT_FLAGS:
                    agent_context[f"is_{flag_name}"] = normalized_flag == flag_name

                # Product-name alias for the q-dev lineage.
                agent_context["is_kiro"] = normalized_name == "q-dev"

                agent_vars["@"] = resolved_prefix
                agent_vars["agent"] = agent_context

            resolved_flags = await resolve_all_flags(session)
            styling_value = resolved_flags.get(FLAG_CONTENT_STYLE, "plain")
        except Exception as e:
            logger.debug(f"Session/agent context failed, using defaults: {e}")

        # Convert to enum and get styling variables
        # Import here to avoid circular dependency with formatters module
        from mcp_guide.content.formatters.selection import TemplateStyling, get_styling_variables

        styling = TemplateStyling.from_flag_value(styling_value)
        formatting_vars = get_styling_variables(styling)

        # Import task_manager once to avoid duplication
        # Import here to avoid circular dependency (render → task_manager → render)
        from mcp_guide.task_manager import get_task_manager

        task_manager = get_task_manager()

        # Add task statistics
        try:
            agent_vars["tasks"] = task_manager.get_task_statistics()
        except (AttributeError, KeyError) as e:
            logger.debug(f"Failed to get task statistics: {e}")

        # Add OpenSpec-specific context (version, changes, status)
        try:
            # OpenSpecTask needs lazy import
            from mcp_guide.openspec.task import OpenSpecTask

            openspec_task_subscriber = task_manager.get_task_by_type(OpenSpecTask)

            if openspec_task_subscriber:
                # Create lambda for version checking
                def has_version(text: str, render: Any) -> bool:
                    """Check if OpenSpec version meets minimum requirement.

                    Args:
                        text: Minimum version string (e.g., "1.2.0")
                        render: Mustache render function

                    Returns:
                        True if current version >= minimum
                    """
                    minimum = render(text).strip()
                    return openspec_task_subscriber.meets_minimum_version(minimum)

                agent_vars["openspec"] = {
                    "available": openspec_task_subscriber.is_available(),
                    "version": openspec_task_subscriber.get_version(),
                    "changes": openspec_task_subscriber.get_changes() or [],
                    "show": openspec_task_subscriber.get_show(),
                    "status": openspec_task_subscriber.get_status(),
                    "has_version": has_version,
                }
            else:
                # Task not registered (feature flag disabled) - set to False
                agent_vars["openspec"] = False
        except Exception as e:
            logger.debug(f"Failed to get OpenSpec context: {e}")
            agent_vars["openspec"] = False

        agent_vars.update(formatting_vars)

        return TemplateContext(agent_vars)

    async def _build_project_context(self) -> "TemplateContext":
        """Build project context with current project data."""
        from mcp_guide.render.context import TemplateContext
        from mcp_guide.session import get_session

        # Extract project information from current session using public API
        project_name = ""
        project_key = ""
        project_hash = ""
        project_flags: dict[str, Any] = {}
        categories_list: list[dict[str, Any]] = []
        collections_list: list[dict[str, Any]] = []
        flags_list: list[dict[str, Any]] = []
        project = None
        project_flag_values = []

        try:
            session = await get_session(None)
            if session:
                project = await session.get_project()

                if project:
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

                    # Convert project flags dict to list format for iteration
                    project_flag_values = [{"key": k, "value": v} for k, v in (project.project_flags or {}).items()]
        except (AttributeError, ValueError, RuntimeError) as e:
            logger.error(f"Failed to get project from session: {e}", exc_info=True)

        # Get global flags for template context
        global_flags_dict = {}
        global_flags_list = []
        try:
            if session:
                global_flags_dict = await session.feature_flags().list()
                global_flags_list = [{"key": k, "value": v} for k, v in global_flags_dict.items()]
        except Exception as e:
            logger.debug(f"Failed to get global flags: {e}")

        # Get resolved flags (project + global with project overrides)
        resolved_flags_dict = {}
        resolved_flags_list = []
        try:
            if session:
                from mcp_guide.models import resolve_all_flags

                resolved_flags_dict = await resolve_all_flags(session)
                resolved_flags_list = [{"key": k, "value": v} for k, v in resolved_flags_dict.items()]
        except Exception as e:
            logger.debug(f"Failed to resolve flags: {e}")

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

        # Get client working directory for template context
        client_working_dir = ""
        try:
            from mcp_guide.mcp_context import resolve_project_path

            client_working_dir = str(await resolve_project_path())
        except Exception as e:
            logger.debug(f"Failed to get client working directory: {e}")

        # Resolve path flags for template context with validation
        path_config = {
            "documents": ".todo/",  # Default
            "export": ".knowledge/",  # Default
        }
        try:
            if session:
                from mcp_guide.feature_flags.constants import FLAG_PATH_DOCUMENTS, FLAG_PATH_EXPORT
                from mcp_guide.feature_flags.utils import get_resolved_flag_value
                from mcp_guide.feature_flags.validators import validate_path_flag

                documents_path = await get_resolved_flag_value(session, FLAG_PATH_DOCUMENTS)
                export_path = await get_resolved_flag_value(session, FLAG_PATH_EXPORT)

                if documents_path and isinstance(documents_path, str) and validate_path_flag(documents_path, True):
                    path_config["documents"] = documents_path
                if export_path and isinstance(export_path, str) and validate_path_flag(export_path, True):
                    path_config["export"] = export_path
        except Exception as e:
            logger.debug(f"Failed to resolve path flags: {e}")

        # Resolve workflow flags for template context
        workflow_config: dict[str, Any] | None = None
        try:
            if session and project:
                from mcp_guide.models import resolve_all_flags

                resolved_flags = await resolve_all_flags(session)

                # Resolve workflow flag
                workflow_flag = resolved_flags.get(FLAG_WORKFLOW)
                if workflow_flag is not None and isinstance(workflow_flag, (bool, list)):
                    parsed_config = parse_workflow_phases(workflow_flag)
                    if parsed_config.enabled:
                        workflow_config = {
                            "phases": parsed_config.phases,
                            "file": DEFAULT_WORKFLOW_FILE,
                        }

                        # Resolve workflow-file flag
                        workflow_file_flag = resolved_flags.get(FLAG_WORKFLOW_FILE)
                        if workflow_file_flag and isinstance(workflow_file_flag, str):
                            # Substitute variables in workflow file path
                            workflow_file = substitute_variables(
                                workflow_file_flag,
                                project_name=project.name,
                                project_key=project.key,
                                project_hash=project.hash,
                            )
                            workflow_config["file"] = workflow_file

                        # Resolve workflow-consent flag (None or dict only)
                        workflow_consent_flag = resolved_flags.get(FLAG_WORKFLOW_CONSENT)
                        if workflow_consent_flag is None:
                            workflow_consent_flag = DEFAULT_WORKFLOW_CONSENT
                        # Transform consent config for template access
                        consent_context = {}
                        phase_names = parsed_config.phases  # List of available phase names
                        ordered_phase_names = parsed_config.ordered_phases
                        for phase_name in phase_names:
                            consent_value = workflow_consent_flag.get(phase_name, [])
                            consent_list = [consent_value] if isinstance(consent_value, str) else consent_value
                            consent_context[phase_name] = {
                                "entry": "entry" in consent_list,
                                "exit": "exit" in consent_list,
                                "any": ("entry" in consent_list) or ("exit" in consent_list),
                            }
                        workflow_config["consent"] = consent_context

                        phases_context: dict[str, Any] = {}
                        for phase_name in phase_names:
                            phase_context: dict[str, Any] = {"enabled": True}
                            if phase_name in ordered_phase_names:
                                current_index = ordered_phase_names.index(phase_name)
                                phase_context["next"] = ordered_phase_names[
                                    (current_index + 1) % len(ordered_phase_names)
                                ]
                                phase_context["ordered"] = True
                            else:
                                phase_context["ordered"] = False
                            phases_context[phase_name] = phase_context
                        workflow_config["phases"] = phases_context
                        workflow_config["phase_list"] = phase_names
                        workflow_config["ordered_phase_list"] = ordered_phase_names

                        # Add boolean flag for each configured phase
                        for phase_name in phase_names:
                            workflow_config[phase_name] = True

                        # Get workflow state from TaskManager cache
                        # Deferred import: avoids circular dependency (tool_decorator → task_manager → render → cache → task_manager)
                        from mcp_guide.task_manager import get_task_manager

                        task_manager = get_task_manager()
                        workflow_state = task_manager.get_cached_data("workflow_state")
                        if workflow_state:
                            # Add parsed workflow state to config
                            workflow_config.update(
                                {
                                    "phase": workflow_state.phase,
                                    "issue": workflow_state.issue,
                                    "tracking": workflow_state.tracking,
                                    "description": workflow_state.description,
                                    "queue": workflow_state.queue,
                                    "issue_is_exploratory": bool(
                                        workflow_state.issue
                                        and workflow_state.issue.startswith("explor")
                                        and workflow_state.phase != "exploration"
                                    ),
                                }
                            )

                            # Calculate next phase
                            try:
                                current_index = ordered_phase_names.index(workflow_state.phase)
                                next_phase = ordered_phase_names[(current_index + 1) % len(ordered_phase_names)]
                                workflow_config["next"] = {"value": next_phase}
                            except ValueError:
                                workflow_config["next"] = None

                            # Add current phase consent flags
                            current_phase_consent = consent_context.get(
                                workflow_state.phase, {"entry": False, "exit": False}
                            )
                            workflow_config["consent"]["entry"] = current_phase_consent["entry"]
                            workflow_config["consent"]["exit"] = current_phase_consent["exit"]
        except Exception as e:
            logger.debug(f"Failed to resolve workflow flags: {e}")

        project_vars = {
            "project": {
                "name": "",  # Default empty name
                "categories": [],  # Default empty categories
                "collections": [],  # Default empty collections
                "project_flag_values": [],  # Default empty flags
                **(project.__dict__ if project else {}),  # Override with actual project data if available
                "categories": categories_list,  # Always use our formatted lists
                "collections": collections_list,
                "project_flag_values": project_flag_values,
            },
            "client_working_dir": client_working_dir,
            "path": path_config,  # Path flags (documents, export)
            "flags": resolved_flags_dict,  # Resolved flags (project + global with overrides)
            "flag_values": resolved_flags_list,  # List format for iteration
            "feature_flags": global_flags_dict,  # Global flags only (dict format)
            "feature_flag_values": global_flags_list,  # Global flags only (list format)
            "projects": projects_data,
            "projects_count": projects_count,
        }

        # Create base context and add workflow configuration as child if enabled
        base_context = TemplateContext(project_vars)
        if workflow_config is not None:
            workflow_vars = {"workflow": workflow_config}
            return base_context.new_child(workflow_vars)
        else:
            return base_context

    async def _build_category_context(self, category_name: str) -> "TemplateContext":
        """Build category context with category data (not cached)."""
        from mcp_guide.render.context import TemplateContext
        from mcp_guide.session import get_session

        # Extract category information from current session's project
        category_data = {"name": "", "dir": "", "patterns": [], "description": ""}
        try:
            session = await get_session(None)
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

    async def get_template_contexts(self, category_name: Optional[str] = None) -> "TemplateContext":
        """Get layered template contexts for rendering.

        Args:
            category_name: Optional category name for category-specific context

        Returns:
            TemplateContext with layered contexts (system → agent → project → category)
        """
        # Check cache first (only for non-category contexts)
        if category_name is None:
            if self._cache is not None:
                logger.trace("TemplateContextCache: Returning cached context")
                return self._cache
            logger.trace("TemplateContextCache: No cached context, building new one")

        # Build contexts
        system_context = await self._build_system_context()
        client_context = await self._build_client_context()
        agent_context = await self._build_agent_context()
        project_context = await self._build_project_context()

        # Create layered context: project → agent → client → system
        layered_context = project_context.new_child(agent_context.new_child(client_context.new_child(system_context)))

        # Add category context if requested (not cached)
        if category_name is not None:
            category_context = await self._build_category_context(category_name)
            layered_context = category_context.new_child(layered_context)
        else:
            # Cache only when no category context (base contexts only)
            self._cache = layered_context

        return layered_context

    def get_transient_context(self) -> "TemplateContext":
        """Generate fresh transient context with timestamps.

        Returns:
            TemplateContext with fresh timestamp data
        """
        import time
        from datetime import datetime, timezone

        from mcp_guide.render.context import TemplateContext

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


def _get_session_cache() -> Optional[TemplateContextCache]:
    """Get the TemplateContextCache from the current session, if available."""
    from mcp_guide.session import get_active_session

    session = get_active_session()
    if session is None:
        return None
    return session.template_cache


def invalidate_template_context_cache() -> None:
    """Invalidate the template context cache for the current session."""
    cache = _get_session_cache()
    if cache:
        cache.invalidate()


def invalidate_template_contexts() -> None:
    """Invalidate the template context cache."""
    invalidate_template_context_cache()
    logger.debug("Template context cache invalidated")


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
    from mcp_guide.render.renderer import is_template_file

    if any(is_template_file(file_info) for file_info in files):
        return await get_template_contexts(category_name)
    return None


async def get_template_contexts(category_name: Optional[str] = None) -> TemplateContext:
    """Public API to get template contexts for rendering.

    Args:
        category_name: Optional category name for category-specific context

    Returns:
        TemplateContext with layered contexts
    """
    cache = _get_session_cache()
    if cache is None:
        # Fallback: create a temporary cache (no session yet)
        cache = TemplateContextCache()
    return await cache.get_template_contexts(category_name)


def get_transient_context() -> TemplateContext:
    """Get transient context with timestamps from the current session's cache."""
    cache = _get_session_cache()
    if cache is None:
        cache = TemplateContextCache()
    return cache.get_transient_context()
