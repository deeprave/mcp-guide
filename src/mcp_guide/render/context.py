"""Template context management with type-safe ChainMap extension."""

import time
from collections import ChainMap
from collections.abc import MutableMapping
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from mcp_guide.core.mcp_log import get_logger

logger = get_logger(__name__)


def convert_lists_to_indexed(obj: Any) -> Any:
    """Recursively convert lists to IndexedList for both iteration and indexed access."""
    if isinstance(obj, list):
        return IndexedList([convert_lists_to_indexed(item) for item in obj])
    elif isinstance(obj, dict):
        return {k: convert_lists_to_indexed(v) for k, v in obj.items()}
    else:
        return obj


class IndexedList(list[Any]):
    """List that supports both iteration and indexed access via attributes."""

    def __init__(self, items: Any) -> None:
        super().__init__()
        processed_items = []
        for i, item in enumerate(items):
            if isinstance(item, dict):
                enhanced_item = item.copy()
                enhanced_item["first"] = i == 0
                enhanced_item["last"] = i == len(items) - 1
                processed_items.append(enhanced_item)
            else:
                processed_items.append({"value": item, "first": (i == 0), "last": (i == len(items) - 1)})

        self.extend(processed_items)

        for i, item in enumerate(processed_items):
            setattr(self, str(i), item)
        setattr(self, "length", len(processed_items))


class TemplateContext(ChainMap[str, Any]):
    """Type-safe template context extending ChainMap for scope chaining."""

    def __init__(self, *maps: dict[str, Any]) -> None:
        converted_maps = [convert_lists_to_indexed(mapping) for mapping in maps]
        for mapping in converted_maps:
            self._validate_mapping(mapping)
        super().__init__(*converted_maps)

    @staticmethod
    def _validate_mapping(mapping: dict[str, Any]) -> None:
        for key in mapping:
            if not isinstance(key, str):
                raise TypeError(f"Context keys must be strings, got {type(key).__name__}: {key}")

    def __setitem__(self, key: str, value: Any) -> None:
        if not isinstance(key, str):
            raise TypeError(f"Context keys must be strings, got {type(key).__name__}: {key}")
        super().__setitem__(key, value)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and super().__contains__(key)

    def new_child(self, m: Optional[MutableMapping[str, Any]] = None) -> "TemplateContext":
        if m is None:
            m = {}
        if isinstance(m, dict):
            self._validate_mapping(m)  # ty: ignore[invalid-argument-type]
        return TemplateContext(m, *self.maps)  # ty: ignore[invalid-argument-type]

    @property
    def parents(self) -> Optional["TemplateContext"]:
        parent_maps = super().parents
        return None if len(self.maps) <= 1 else TemplateContext(*parent_maps.maps)  # ty: ignore[invalid-argument-type]


def _convert_to_template_safe(value: Any) -> Any:
    """Convert value to template-safe representation."""
    if value is None:
        return ""
    if isinstance(value, dict):
        return {k: _convert_to_template_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_convert_to_template_safe(item) for item in value]
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return value if isinstance(value, (str, int, float, bool)) else str(value)


def get_transient_context(base_context: TemplateContext) -> TemplateContext:
    """Generate fresh transient data for template rendering."""
    transient_data = {
        "now": datetime.now().isoformat(),
        "timestamp": int(time.time()),
    }
    return base_context.new_child(transient_data)
