"""GuideMCP - Extended FastMCP server with agent info caching."""

from typing import TYPE_CHECKING, Any, Optional

from mcp.server import FastMCP

if TYPE_CHECKING:
    from mcp_guide.agent_detection import AgentInfo


class GuideMCP(FastMCP):
    """Extended FastMCP with agent info caching.

    Adds agent_info attribute to cache client/agent information
    across tool calls within a session.
    """

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(name, *args, **kwargs)
        self.agent_info: Optional["AgentInfo"] = None
