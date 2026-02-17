# Agent Configurations

This directory contains specialised agent configurations for various agentic CLIs. Each subdirectory contains agent definitions for a specific CLI tool.

## Installation

```bash
# Install agents for a specific CLI
guide-agent-install <agent> <dirname>

# Examples
guide-agent-install kiro ~           # Install kiro agents to ~/.kiro/agents/
guide-agent-install kiro .           # Install kiro agents to ./.kiro/agents/
guide-agent-install kiro /path/dir   # Install kiro agents to /path/dir/.kiro/agents/
```

## Available Agent Sets

### kiro

Agent configurations for [Kiro CLI](https://github.com/aws/amazon-q-developer-cli). See [kiro/README.md](kiro/README.md) for detailed documentation.

**Agents**:
- `guide` - Structured development workflow with phase-based progression
- `guide-review` - Code review focusing on correctness, security, and consistency
- `guide-spec` - Requirements gathering and OpenSpec specification authoring

### claude

Agent configurations for [Claude Code](https://code.claude.com/). See [claude/README.md](claude/README.md) for detailed documentation.

**Agents**:
- `guide` - Structured development workflow with phase-based progression
- `guide-review` - Code review focusing on correctness, security, and consistency
- `guide-spec` - Requirements gathering and OpenSpec specification authoring

### copilot

Agent configurations for [GitHub Copilot](https://github.com/features/copilot). See [copilot/README.md](copilot/README.md) for detailed documentation.

**Agents**:
- `guide` - Structured development workflow with phase-based progression
- `guide-review` - Code review focusing on correctness, security, and consistency
- `guide-spec` - Requirements gathering and OpenSpec specification authoring

## Common Concepts

### Resources

Agents typically have access to:
- Project documentation (`README.md`, `AGENTS.md`)
- OpenSpec documentation (`openspec/AGENTS.md`)
- Project and user-specific rules (`.kiro/rules/**/*.md`, `~/.kiro/rules/**/*.md`)

### Agent Purposes

Agents are designed for specific workflows:
- **Development workflow agent**: Guide through structured development phases
- **Review agent**: Analyse code changes for issues and improvements
- **Specification agent**: Create/maintain technical specs and documentation

Each agent set may have different capabilities and tool access depending on the CLI tool they're designed for.
