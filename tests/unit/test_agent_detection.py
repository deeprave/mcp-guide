"""Tests for agent detection logic."""

from mcp_guide.agent_detection import AgentInfo, detect_agent, format_agent_info, normalize_agent_name


def test_agent_info_dataclass():
    """Test AgentInfo dataclass creation."""
    agent = AgentInfo(name="Kiro CLI", normalized_name="kiro", version="1.0.0", prompt_prefix="@")

    assert agent.name == "Kiro CLI"
    assert agent.normalized_name == "kiro"
    assert agent.version == "1.0.0"
    assert agent.prompt_prefix == "@"


def test_agent_info_optional_version():
    """Test AgentInfo with None version."""
    agent = AgentInfo(name="Unknown Agent", normalized_name="unknown", version=None, prompt_prefix="/")

    assert agent.version is None


def test_normalize_agent_name_kiro():
    """Test normalizing Kiro agent names."""
    assert normalize_agent_name("Kiro CLI") == "kiro"
    assert normalize_agent_name("kiro") == "kiro"
    assert normalize_agent_name("KIRO") == "kiro"


def test_normalize_agent_name_claude():
    """Test normalizing Claude agent names."""
    assert normalize_agent_name("Claude Desktop") == "claude"
    assert normalize_agent_name("claude") == "claude"


def test_normalize_agent_name_copilot():
    """Test normalizing Copilot agent names."""
    assert normalize_agent_name("GitHub Copilot") == "copilot"
    assert normalize_agent_name("copilot") == "copilot"


def test_normalize_agent_name_unknown():
    """Test normalising unknown agent names uses presented name."""
    assert normalize_agent_name("Unknown Agent") == "unknown-agent"
    assert normalize_agent_name("Some New Tool") == "some-new-tool"
    assert normalize_agent_name("mcp") == "mcp"
    assert normalize_agent_name("My Custom Agent") == "my-custom-agent"


def test_normalize_agent_name_edge_cases():
    """Test normalising agent names with edge cases."""
    # Empty and whitespace-only strings
    assert normalize_agent_name("") == "unknown"
    assert normalize_agent_name("   ") == "unknown"
    assert normalize_agent_name("\t\n") == "unknown"

    # Multiple consecutive spaces
    assert normalize_agent_name("Multiple   Spaces") == "multiple-spaces"
    assert normalize_agent_name("Too    Many     Spaces") == "too-many-spaces"

    # Special characters
    assert normalize_agent_name("Special!@#Chars") == "specialchars"
    assert normalize_agent_name("Agent-Name") == "agent-name"
    assert normalize_agent_name("Agent_Name") == "agentname"

    # Leading/trailing spaces and hyphens
    assert normalize_agent_name("  Leading Spaces") == "leading-spaces"
    assert normalize_agent_name("Trailing Spaces  ") == "trailing-spaces"

    # Only special characters (reduces to empty)
    assert normalize_agent_name("!!!") == "unknown"
    assert normalize_agent_name("@@@") == "unknown"
    assert normalize_agent_name("---") == "unknown"
    assert normalize_agent_name("-Hyphen-Name-") == "hyphen-name"

    # Mixed cases
    assert normalize_agent_name("My-Agent 2.0!") == "my-agent-20"
    assert normalize_agent_name("Agent (Beta)") == "agent-beta"


def test_normalize_agent_name_q_dev():
    """Test normalizing Q Dev agent names."""
    assert normalize_agent_name("Q Dev") == "q-dev"
    assert normalize_agent_name("q dev") == "q-dev"
    assert normalize_agent_name("Q  Dev") == "q-dev"


def test_normalize_agent_name_gemini():
    """Test normalizing Gemini agent names."""
    assert normalize_agent_name("Google Gemini") == "gemini"
    assert normalize_agent_name("gemini") == "gemini"
    assert normalize_agent_name("Gemini") == "gemini"


def test_normalize_agent_name_windsurf():
    """Test normalizing Windsurf agent names."""
    assert normalize_agent_name("Windsurf") == "windsurf"
    assert normalize_agent_name("Cascade") == "windsurf"
    assert normalize_agent_name("windsurf") == "windsurf"


def test_detect_agent_kiro():
    """Test detecting Kiro agent."""
    client_params = {"clientInfo": {"name": "Kiro CLI", "version": "1.0.0"}}

    agent = detect_agent(client_params)
    assert agent.name == "Kiro CLI"
    assert agent.normalized_name == "kiro"
    assert agent.version == "1.0.0"
    assert agent.prompt_prefix == "@"


def test_detect_agent_claude():
    """Test detecting Claude agent."""
    client_params = {"clientInfo": {"name": "Claude Desktop", "version": "2.0.0"}}

    agent = detect_agent(client_params)
    assert agent.name == "Claude Desktop"
    assert agent.normalized_name == "claude"
    assert agent.version == "2.0.0"
    assert agent.prompt_prefix == "/"


def test_detect_agent_no_version():
    """Test detecting agent without version."""
    client_params = {"clientInfo": {"name": "Kiro CLI"}}

    agent = detect_agent(client_params)
    assert agent.version is None


def test_detect_agent_unknown():
    """Test detecting unknown agent uses presented name."""
    client_params = {"clientInfo": {"name": "Unknown Tool"}}

    agent = detect_agent(client_params)
    assert agent.normalized_name == "unknown-tool"
    assert agent.prompt_prefix == "/"


def test_detect_agent_with_pydantic_model():
    """Test detecting agent from InitializeRequestParams object."""
    from mcp.types import Implementation

    # Create a mock object that mimics InitializeRequestParams
    class MockClientParams:
        def __init__(self):
            self.clientInfo = Implementation(name="Kiro CLI", version="1.0.0")

    client_params = MockClientParams()

    agent = detect_agent(client_params)
    assert agent.name == "Kiro CLI"
    assert agent.normalized_name == "kiro"
    assert agent.version == "1.0.0"
    assert agent.prompt_prefix == "@"


def test_detect_agent_with_none_client_info():
    """Test detecting agent when clientInfo is None."""

    class MockClientParams:
        def __init__(self):
            self.clientInfo = None

    client_params = MockClientParams()

    agent = detect_agent(client_params)
    assert agent.name == "Unknown"
    assert agent.normalized_name == "unknown"
    assert agent.version is None


def test_detect_agent_with_empty_dict():
    """Test detecting agent with empty dict (no clientInfo)."""
    client_params = {}

    agent = detect_agent(client_params)
    assert agent.name == "Unknown"
    assert agent.normalized_name == "unknown"
    assert agent.version is None
    assert agent.prompt_prefix == "/"


def test_detect_agent_with_non_dict_non_object():
    """Test detecting agent with non-dict, non-object input."""
    # Test with various invalid inputs
    for invalid_input in [123, "string", None, []]:
        agent = detect_agent(invalid_input)
        assert agent.name == "Unknown"
        assert agent.normalized_name == "unknown"
        assert agent.version is None
        assert agent.prompt_prefix == "/"


def test_format_agent_info_with_version():
    """Test formatting agent info with version."""
    agent = AgentInfo(name="Kiro CLI", normalized_name="kiro", version="1.0.0", prompt_prefix="@")

    formatted = format_agent_info(agent, "mcp-guide")
    assert "Kiro CLI" in formatted
    assert "1.0.0" in formatted
    assert "@" in formatted


def test_format_agent_info_without_version():
    """Test formatting agent info without version."""
    agent = AgentInfo(name="Kiro CLI", normalized_name="kiro", version=None, prompt_prefix="@")

    formatted = format_agent_info(agent, "mcp-guide")
    assert "Kiro CLI" in formatted
    assert "@" in formatted


def test_format_agent_info_claude_prefix():
    """Test formatting Claude agent with mcp_name substitution."""
    agent = AgentInfo(name="Claude Desktop", normalized_name="claude", version="2.0.0", prompt_prefix="/{mcp_name}:")

    formatted = format_agent_info(agent, "mcp-guide")
    assert "Claude Desktop" in formatted
    assert "/mcp-guide:" in formatted
