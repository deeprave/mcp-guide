"""Expression parsing for document references."""

from typing import NamedTuple, Optional


class DocumentExpression(NamedTuple):
    """Document expression for parsing user input before resolution.

    Used to parse category/pattern syntax with lenient validation.
    Resolution logic determines if name refers to category or collection.

    Attributes:
        raw_input: Original user input string
        name: Parsed category or collection name
        patterns: Optional list of parsed patterns
    """

    raw_input: str
    name: str
    patterns: Optional[list[str]] = None
