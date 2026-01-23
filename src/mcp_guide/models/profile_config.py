"""Profile configuration dataclasses."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProfileCategory:
    """Category configuration for profiles."""

    name: str
    patterns: list[str]
    dir: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ProfileCollection:
    """Collection configuration for profiles."""

    name: str
    categories: list[str]
    description: Optional[str] = None
