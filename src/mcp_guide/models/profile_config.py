"""Profile configuration dataclasses."""

from dataclasses import dataclass
from typing import Optional

from mcp_guide.core.validation import validate_reserved_content_name_prefix


@dataclass
class ProfileCategory:
    """Category configuration for profiles."""

    name: str
    patterns: list[str]
    dir: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self) -> None:
        validate_reserved_content_name_prefix(self.name, "Category")


@dataclass
class ProfileCollection:
    """Collection configuration for profiles."""

    name: str
    categories: list[str]
    description: Optional[str] = None

    def __post_init__(self) -> None:
        validate_reserved_content_name_prefix(self.name, "Collection")
