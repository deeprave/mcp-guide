"""Tests for agent detection logic."""

import pytest

from mcp_guide.agent_detection import AgentInfo, detect_agent, format_agent_info, normalize_agent_name


@pytest.mark.parametrize(
    ("presented", "expected"),
    [
        ("Kiro CLI", "q-dev"),
        ("kiro", "q-dev"),
        ("KIRO", "q-dev"),
        ("Claude Desktop", "claude"),
        ("claude", "claude"),
        ("GitHub Copilot", "copilot"),
        ("copilot", "copilot"),
        ("codex-mcp-client", "codex"),
        ("Codex CLI", "codex"),
        ("Q Dev", "q-dev"),
        ("q dev", "q-dev"),
        ("Q  Dev", "q-dev"),
        ("Google Gemini", "gemini"),
        ("gemini", "gemini"),
        ("Gemini", "gemini"),
        ("Windsurf", "windsurf"),
        ("Cascade", "windsurf"),
        ("windsurf", "windsurf"),
        ("Cursor", "cursor"),
        ("cursor-agent", "cursor"),
        ("Pi", "pi"),
        ("pi-mcp-guide", "pi"),
        ("opencode-ai", "opencode"),
        ("opencode", "opencode"),
        ("Unknown Agent", "unknown-agent"),
        ("Some New Tool", "some-new-tool"),
        ("mcp", "mcp"),
        ("My Custom Agent", "my-custom-agent"),
        ("", "unknown"),
        ("   ", "unknown"),
        ("\t\n", "unknown"),
        ("Multiple   Spaces", "multiple-spaces"),
        ("Too    Many     Spaces", "too-many-spaces"),
        ("Special!@#Chars", "specialchars"),
        ("Agent-Name", "agent-name"),
        ("Agent_Name", "agentname"),
        ("  Leading Spaces", "leading-spaces"),
        ("Trailing Spaces  ", "trailing-spaces"),
        ("!!!", "unknown"),
        ("@@@", "unknown"),
        ("---", "unknown"),
        ("-Hyphen-Name-", "hyphen-name"),
        ("My-Agent 2.0!", "my-agent-20"),
        ("Agent (Beta)", "agent-beta"),
    ],
    ids=lambda value: value or "empty",
)
def test_normalize_agent_name(presented: str, expected: str) -> None:
    """Normalise aliases and free-form names to stable agent identifiers."""
    assert normalize_agent_name(presented) == expected


class TestAgentDetection:
    def test_detect_agent_kiro(self):
        """Test detecting Kiro agent."""
        client_params = {"clientInfo": {"name": "Kiro CLI", "version": "1.0.0"}}

        agent = detect_agent(client_params)
        assert agent.name == "Kiro CLI"
        assert agent.normalized_name == "q-dev"
        assert agent.version == "1.0.0"
        assert agent.prompt_prefix == "@"

    def test_detect_agent_claude(self):
        """Test detecting Claude agent."""
        client_params = {"clientInfo": {"name": "Claude Desktop", "version": "2.0.0"}}

        agent = detect_agent(client_params)
        assert agent.name == "Claude Desktop"
        assert agent.normalized_name == "claude"
        assert agent.version == "2.0.0"
        assert agent.prompt_prefix == "/"

    def test_detect_agent_codex(self):
        """Test detecting Codex agent."""
        client_params = {"clientInfo": {"name": "codex-mcp-client", "version": "0.116.0"}}

        agent = detect_agent(client_params)
        assert agent.name == "codex-mcp-client"
        assert agent.normalized_name == "codex"
        assert agent.version == "0.116.0"
        assert agent.prompt_prefix is None

    def test_detect_agent_cursor_has_no_prompt_prefix(self):
        """Cursor Agent does not support direct prompt invocation."""
        agent = detect_agent({"clientInfo": {"name": "Cursor", "version": "1.0.0"}})

        assert agent.normalized_name == "cursor"
        assert agent.prompt_prefix is None

    def test_detect_agent_pi_has_no_prompt_prefix(self):
        """Pi MCP Guide clients normalize to Pi without a prompt prefix."""
        agent = detect_agent({"clientInfo": {"name": "pi-mcp-guide", "version": "1.0.0"}})

        assert agent.normalized_name == "pi"
        assert agent.prompt_prefix is None

    def test_detect_agent_no_version(self):
        """Test detecting agent without version."""
        client_params = {"clientInfo": {"name": "Kiro CLI"}}

        agent = detect_agent(client_params)
        assert agent.version is None

    def test_detect_agent_unknown(self):
        """Test detecting unknown agent uses presented name."""
        client_params = {"clientInfo": {"name": "Unknown Tool"}}

        agent = detect_agent(client_params)
        assert agent.normalized_name == "unknown-tool"
        assert agent.prompt_prefix is None

    def test_detect_agent_with_pydantic_model(self):
        """Test detecting agent from InitializeRequestParams object."""
        from mcp.types import Implementation

        class MockClientParams:
            def __init__(self):
                self.clientInfo = Implementation(name="Kiro CLI", version="1.0.0")

        agent = detect_agent(MockClientParams())
        assert agent.name == "Kiro CLI"
        assert agent.normalized_name == "q-dev"
        assert agent.version == "1.0.0"
        assert agent.prompt_prefix == "@"

    def test_detect_agent_with_none_client_info(self):
        """Test detecting agent when clientInfo is None."""

        class MockClientParams:
            def __init__(self):
                self.clientInfo = None

        agent = detect_agent(MockClientParams())
        assert agent.name == "Unknown"
        assert agent.normalized_name == "unknown"
        assert agent.version is None

    def test_detect_agent_with_empty_dict(self):
        """Test detecting agent with empty dict (no clientInfo)."""
        agent = detect_agent({})

        assert agent.name == "Unknown"
        assert agent.normalized_name == "unknown"
        assert agent.version is None
        assert agent.prompt_prefix is None

    def test_detect_agent_with_non_dict_non_object(self):
        """Test detecting agent with non-dict, non-object input."""
        for invalid_input in [123, "string", None, []]:
            agent = detect_agent(invalid_input)
            assert agent.name == "Unknown"
            assert agent.normalized_name == "unknown"
            assert agent.version is None
            assert agent.prompt_prefix is None


class TestAgentInfoFormatting:
    def test_format_agent_info_with_version(self):
        """Test formatting agent info with version."""
        agent = AgentInfo(name="Kiro CLI", normalized_name="q-dev", version="1.0.0", prompt_prefix="@")

        formatted = format_agent_info(agent, "mcp-guide")
        assert "Kiro CLI" in formatted
        assert "1.0.0" in formatted
        assert "@" in formatted

    def test_format_agent_info_without_version(self):
        """Test formatting agent info without version."""
        agent = AgentInfo(name="Kiro CLI", normalized_name="q-dev", version=None, prompt_prefix="@")

        formatted = format_agent_info(agent, "mcp-guide")
        assert "Kiro CLI" in formatted
        assert "@" in formatted

    def test_format_agent_info_claude_prefix(self):
        """Test formatting Claude agent with mcp_name substitution."""
        agent = AgentInfo(
            name="Claude Desktop", normalized_name="claude", version="2.0.0", prompt_prefix="/{mcp_name}:"
        )

        formatted = format_agent_info(agent, "mcp-guide")
        assert "Claude Desktop" in formatted
        assert "/mcp-guide:" in formatted

    def test_format_agent_info_codex_prefix_none(self):
        """Test formatting Codex agent with no prompt prefix."""
        agent = AgentInfo(name="codex-mcp-client", normalized_name="codex", version="0.116.0", prompt_prefix=None)

        formatted = format_agent_info(agent, "guide")
        assert "codex-mcp-client" in formatted
        assert "Command Prefix: None" in formatted
