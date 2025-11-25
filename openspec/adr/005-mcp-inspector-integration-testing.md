# ADR-005: MCP Inspector for Integration Testing

**Date:** 2025-11-25
**Status:** Decided
**Deciders:** Development Team

## Context

Need a reliable way to perform integration testing of MCP server functionality without requiring a full AI agent client. Testing should be:
- Automated and scriptable
- Runnable in CI/CD pipelines
- Able to validate MCP protocol compliance
- Easy to integrate with pytest

## Decision

Use MCP Inspector CLI mode for integration testing of the MCP server.

## Rationale

**MCP Inspector Advantages:**
- **Official Tool**: Maintained by the MCP protocol team
- **CLI Mode**: Non-interactive mode perfect for automation (`--cli` flag)
- **Python Package**: Available as `mcp-inspector` on PyPI
- **Protocol Validation**: Ensures proper MCP protocol implementation
- **Comprehensive Testing**: Can test tools, prompts, and resources
- **CI/CD Ready**: Scriptable and automatable

**Alternatives Considered:**
- **Manual Testing**: Not scalable, error-prone
- **Mock MCP Protocol**: Complex, doesn't validate real protocol compliance
- **Custom Test Client**: Reinventing the wheel, maintenance burden

## Implementation

### Installation

Add to development dependencies:
```bash
uv add --dev mcp-inspector
```

### pytest Integration

```python
# tests/conftest.py

import subprocess
import pytest
from pathlib import Path

@pytest.fixture
def mcp_server():
    """Start MCP server for testing"""
    process = subprocess.Popen(
        ["uv", "run", "mcp-guide"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    yield process
    process.terminate()
    process.wait()

@pytest.fixture
def mcp_inspector(mcp_server):
    """MCP Inspector CLI interface"""
    # Use mcp-inspector CLI to interact with server
    # Return helper object for making inspector calls
    pass
```

### Integration Test Example

```python
# tests/integration/test_server_startup.py

def test_server_responds_to_handshake(mcp_inspector):
    """Test that server responds to MCP protocol handshake"""
    response = mcp_inspector.initialize()
    assert response["success"]
    assert response["serverInfo"]["name"] == "mcp-guide"
    assert response["serverInfo"]["version"] == "0.5.0"

def test_server_lists_capabilities(mcp_inspector):
    """Test that server advertises its capabilities"""
    response = mcp_inspector.list_capabilities()
    assert "tools" in response["capabilities"]
    assert "prompts" in response["capabilities"]
    assert "resources" in response["capabilities"]
```

### CLI Usage

```bash
# Manual testing
mcp-inspector --cli uv run mcp-guide

# Automated testing in CI
pytest tests/integration/
```

## Consequences

### Positive

- **Reliable Testing**: Official tool ensures protocol compliance
- **Easy Integration**: Python package integrates seamlessly with pytest
- **Automation Ready**: CLI mode perfect for CI/CD
- **Comprehensive**: Tests entire MCP protocol surface
- **Maintenance**: Tool maintained by MCP team, not us

### Negative

- **External Dependency**: Requires mcp-inspector package
- **Node.js Alternative**: npm version also available if needed
- **Learning Curve**: Need to understand inspector CLI interface

### Neutral

- **Test Coverage**: Complements unit tests, doesn't replace them
- **Performance**: Integration tests slower than unit tests (expected)

## Testing Strategy

### Unit Tests
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast, focused tests

### Integration Tests (MCP Inspector)
- Test MCP protocol compliance
- Test tool/prompt/resource registration
- Test end-to-end workflows
- Validate server behavior

### Manual Testing
- Use MCP Inspector web UI for exploratory testing
- Test with real AI clients (Claude Desktop, Kiro CLI)

## Status

Decided - to be implemented as part of test infrastructure setup.

## References

- MCP Inspector: https://modelcontextprotocol.io/docs/tools/inspector
- PyPI Package: https://pypi.org/project/mcp-inspector/
- CLI Mode Guide: https://dev.to/yigit-konur/the-ultimate-guide-to-the-mcp-inspector-by-cli-non-interactive-mode-4k6b
