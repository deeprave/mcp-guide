"""Guide prompt arguments implementation."""

from typing import List, Optional

from mcp_core.arguments import Arguments


class GuidePromptArguments(Arguments):
    """Arguments for the @guide prompt.

    The guide prompt provides direct access to guide content without agent interpretation.
    For MVP, only the command parameter is used to call get_content directly.
    """

    command: Optional[str] = None
    """Category or pattern to retrieve content for (e.g., 'guide', 'lang/python')"""

    arguments: List[str] = []
    """Additional arguments reserved for future use"""
