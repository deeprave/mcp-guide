"""Template context management with type-safe ChainMap extension."""

import logging
import time
from collections import ChainMap
from collections.abc import MutableMapping
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

if TYPE_CHECKING:
    from mcp_guide.utils.file_discovery import FileInfo

logger = logging.getLogger(__name__)


# Sentinel object for soft deletion masking
_SOFT_DELETE_SENTINEL = object()


class TemplateContext(ChainMap[str, Any]):
    """Type-safe template context extending ChainMap for scope chaining."""

    def __init__(self, *maps: dict[str, Any]) -> None:
        """Initialize TemplateContext with optional initial mappings."""
        # Validate all keys in initial mappings
        for mapping in maps:
            self._validate_mapping(mapping)
        super().__init__(*maps)

    def _validate_mapping(self, mapping: dict[str, Any]) -> None:
        """Validate that all keys are strings."""
        for key in mapping.keys():
            if not isinstance(key, str):
                raise TypeError(f"Context keys must be strings, got {type(key).__name__}: {key}")

    def __setitem__(self, key: str, value: Any) -> None:
        """Set item with key validation."""
        if not isinstance(key, str):
            raise TypeError(f"Context keys must be strings, got {type(key).__name__}: {key}")
        super().__setitem__(key, value)

    def new_child(self, m: Optional[MutableMapping[str, Any]] = None) -> "TemplateContext":
        """Create new child context, returning TemplateContext instance."""
        if m is None:
            m = {}
        if isinstance(m, dict):
            self._validate_mapping(m)
        return TemplateContext(m, *self.maps)  # type: ignore[arg-type]

    @property
    def parents(self) -> Optional["TemplateContext"]:  # type: ignore[override]
        """Return parent contexts as TemplateContext or None if root."""
        parent_maps = super().parents
        # ChainMap always has at least one map, check if it's meaningful
        if len(self.maps) <= 1:  # Only one map means this is root
            return None
        return TemplateContext(*parent_maps.maps)  # type: ignore[arg-type]

    def __getitem__(self, key: str) -> Any:
        """Get item with soft deletion sentinel handling."""
        value = super().__getitem__(key)
        if value is _SOFT_DELETE_SENTINEL:
            raise KeyError(key)
        return value

    def soft_delete(self, key: str) -> None:
        """Soft delete a key by masking it with sentinel value."""
        if not isinstance(key, str):
            raise TypeError(f"Context keys must be strings, got {type(key).__name__}: {key}")
        self.maps[0][key] = _SOFT_DELETE_SENTINEL

    def hard_delete(self, key: str) -> None:
        """Hard delete a key from current map, revealing parent value if any."""
        if not isinstance(key, str):
            raise TypeError(f"Context keys must be strings, got {type(key).__name__}: {key}")
        self.maps[0].pop(key, None)


def _convert_to_template_safe(value: Any) -> Union[str, int, float, bool]:
    """Convert value to template-safe representation."""
    if value is None:
        return ""
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _validate_and_convert_data(data: Any) -> Dict[str, Any]:
    """Validate and convert data to template-safe format."""
    if not isinstance(data, dict):
        return {}

    result = {}
    for key, value in data.items():
        if isinstance(key, str):
            result[key] = _convert_to_template_safe(value)
        else:
            logger.warning(
                "Dropping non-string key in template context: %r (type: %s)",
                key,
                type(key).__name__,
                extra={"dropped_key": key, "key_type": type(key).__name__, "component": "template_context"},
            )
    return result


def build_template_context(
    system_data: Optional[Dict[str, Any]] = None,
    agent_data: Optional[Dict[str, Any]] = None,
    project_data: Optional[Dict[str, Any]] = None,
    collection_data: Optional[Dict[str, Any]] = None,
    category_data: Optional[Dict[str, Any]] = None,
) -> TemplateContext:
    """Build base template context with static data sources.

    Priority order (highest to lowest): collection > category > project > agent > system
    Note: file_data is added per-file using new_child() during rendering loop
    """
    # Convert and validate all data sources
    layers = []

    # Add layers in highest to lowest priority order (ChainMap uses first-wins)
    if collection_data:
        layers.append(_validate_and_convert_data(collection_data))
    if category_data:
        layers.append(_validate_and_convert_data(category_data))
    if project_data:
        layers.append(_validate_and_convert_data(project_data))
    if agent_data:
        layers.append(_validate_and_convert_data(agent_data))
    if system_data:
        layers.append(_validate_and_convert_data(system_data))

    # Create base context (file context added per-file via new_child)
    return TemplateContext(*layers)


def add_file_context(base_context: TemplateContext, file_info: "FileInfo") -> TemplateContext:
    """Add file-specific context as child of base context for per-file rendering.

    This creates a new child context with file data having highest priority.
    Used in rendering loops where each file gets its own context.
    """
    # Extract template-safe data directly from FileInfo
    file_data = {
        "path": file_info.basename,  # Rendered file path (without .mustache)
        "size": file_info.size,
    }

    # Add mtime with error handling
    try:
        file_data["mtime"] = file_info.mtime.isoformat()
    except (AttributeError, ValueError) as e:
        logger.warning(
            "Failed to convert file mtime to ISO format: %s",
            str(e),
            extra={"file_path": file_info.basename, "mtime_value": file_info.mtime, "component": "template_context"},
        )
        file_data["mtime"] = ""

    # Add optional fields if present
    if file_info.category:
        file_data["category"] = file_info.category
    if file_info.collection:
        file_data["collection"] = file_info.collection
    if file_info.ctime:
        try:
            file_data["ctime"] = file_info.ctime.isoformat()
        except (AttributeError, ValueError) as e:
            logger.warning(
                "Failed to convert file ctime to ISO format: %s",
                str(e),
                extra={
                    "file_path": file_info.basename,
                    "ctime_value": file_info.ctime,
                    "component": "template_context",
                },
            )
            file_data["ctime"] = ""

    return base_context.new_child(file_data)


def get_transient_context(base_context: TemplateContext) -> TemplateContext:
    """Generate fresh transient data for template rendering.

    Creates a new child context with runtime data that must be computed per-render.
    This ensures timestamps and other dynamic values are always current.
    """
    transient_data = {
        "now": datetime.now().isoformat(),
        "timestamp": int(time.time()),
    }
    return base_context.new_child(transient_data)
