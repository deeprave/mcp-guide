"""Agent detection and information formatting."""

import re
from dataclasses import dataclass
from typing import Any, Optional, Union


@dataclass
class AgentInfo:
    """Information about the MCP client/agent."""

    name: str
    normalized_name: str
    version: Optional[str]
    prompt_prefix: str


AGENT_PATTERNS = [
    (r"q\s+dev", "q-dev"),
    (r"kiro", "kiro"),
    (r"claude", "claude"),
    (r"copilot", "copilot"),
    (r"gemini", "gemini"),
    (r"cascade|windsurf", "windsurf"),
]

AGENT_PREFIX_MAP = {
    "q-dev": "@",
    "kiro": "@",
    "claude": "/{mcp_name}:",
    "copilot": "/",
    "gemini": "/",
    "windsurf": "/",
    "unknown": "/",
}


def normalize_agent_name(name: str) -> str:
    """Normalise agent name to lowercase canonical form."""
    # Strip and validate input
    name = name.strip()
    if not name:
        return "unknown"

    name_lower = name.lower()

    for pattern, normalized in AGENT_PATTERNS:
        if re.search(pattern, name_lower):
            return normalized

    # Normalize whitespace: collapse multiple spaces to single hyphen
    normalized = re.sub(r"\s+", "-", name_lower)
    # Remove special characters except hyphens
    normalized = re.sub(r"[^a-z0-9-]", "", normalized)
    # Remove leading/trailing hyphens
    normalized = normalized.strip("-")

    return normalized if normalized else "unknown"


def detect_agent(client_params: Union[dict[str, Any], Any]) -> AgentInfo:
    """Detect agent from client parameters.

    Args:
        client_params: Either InitializeRequestParams object or dict with clientInfo

    Returns:
        AgentInfo with detected agent information
    """
    # Handle Pydantic model (InitializeRequestParams)
    if hasattr(client_params, "clientInfo"):
        client_info = client_params.clientInfo
        name = client_info.name if client_info else "Unknown"
        version = client_info.version if client_info else None
    # Handle dict format (for tests)
    elif isinstance(client_params, dict):
        client_info = client_params.get("clientInfo", {})
        name = client_info.get("name", "Unknown")
        version = client_info.get("version")
    else:
        name = "Unknown"
        version = None

    normalized_name = normalize_agent_name(name)
    prompt_prefix = AGENT_PREFIX_MAP.get(normalized_name, "/")

    return AgentInfo(name=name, normalized_name=normalized_name, version=version, prompt_prefix=prompt_prefix)


def format_agent_info(agent_info: AgentInfo, mcp_name: str) -> str:
    """Format agent info for display."""
    prompt_prefix = agent_info.prompt_prefix.replace("{mcp_name}", mcp_name)

    lines = [
        f"Agent: {agent_info.name}",
        f"Normalised Name: {agent_info.normalized_name}",
    ]

    if agent_info.version:
        lines.append(f"Version: {agent_info.version}")

    lines.append(f"Command Prefix: {prompt_prefix}")

    return "\n".join(lines)
