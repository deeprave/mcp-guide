"""Type-safe frontmatter dictionary."""

from typing import Any, Dict, List, Optional


class Frontmatter(dict[str, Any]):
    """Type-safe frontmatter dictionary with typed accessors."""

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get string value, converting to lowercase if present."""
        value = self.get(key, default)
        if value is None:
            return None
        if isinstance(value, str):
            return value.lower()
        raise TypeError(f"Expected str for key '{key}', got {type(value).__name__}")

    def get_list(self, key: str, default: Optional[List[str]] = None) -> Optional[List[str]]:
        """Get list value, wrapping single values in a list."""
        value = self.get(key, default)
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    def get_dict(self, key: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Get dict value."""
        value = self.get(key, default)
        if value is None or isinstance(value, dict):
            return value
        raise TypeError(f"Expected dict for key '{key}', got {type(value).__name__}")

    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """Get boolean value."""
        value = self.get(key, default)
        if value is None or isinstance(value, bool):
            return value
        raise TypeError(f"Expected bool for key '{key}', got {type(value).__name__}")
