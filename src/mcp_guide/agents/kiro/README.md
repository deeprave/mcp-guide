# Kiro Agent Configurations

Specialised agent configurations for [Kiro CLI](https://github.com/aws/amazon-q-developer-cli).

## Installation

```bash
# Install to home directory
guide-agent-install kiro ~

# Install to current directory
guide-agent-install kiro .

# Install to specific directory
guide-agent-install kiro /path/to/project
```

Installs agents to `<dirname>/.kiro/agents/`.

## Available Agents

### guide
**Purpose**: Structured development workflow with phase-based progression

The `guide` agent enforces a disciplined development cycle through five distinct phases:
- **discussion**: Requirements gathering and problem exploration
- **planning**: Creating implementation plans and specifications
- **implementation**: Code changes (requires explicit consent)
- **check**: Automated testing and verification
- **review**: Final review before completion (requires explicit consent)

**Key Features**:
- Tracks progress via `.guide.yaml` file
- Requires explicit consent for implementation and review phases
- Prevents code changes during discussion/planning phases
- Integrates with OpenSpec for specifications

**Resources**:
- `README.md`, `AGENTS.md`, `openspec/AGENTS.md`
- `.kiro/rules/**/*.md` (project and user rules)

**Pre-trusted Tools**: All standard tools plus git, guide, github, context7, sequentialthinking, and atlassian MCP servers

---

### guide-review
**Purpose**: Code review focusing on correctness, security, and consistency

The `guide-review` agent performs thorough code reviews by comparing working tree changes against HEAD, analysing them for:
- **Critical Issues**: Security vulnerabilities, logic errors, crashes
- **Warnings**: Edge cases, resource leaks, performance problems, inconsistencies
- **Notes**: Alternative approaches, documentation suggestions, test ideas

**Key Features**:
- Compares changes against existing codebase patterns
- Categorises issues by severity (Critical/Warning/Notes)
- Respects project conventions rather than imposing external standards
- Provides specific file/line references and concrete fixes

**Resources**:
- `README.md`, `AGENTS.md`, `openspec/AGENTS.md`
- `.kiro/rules/**/*.md` (project rules only)

**Pre-trusted Tools**: Same as `guide` agent

---

### guide-spec
**Purpose**: Requirements gathering and OpenSpec specification authoring

The `guide-spec` agent specialises in systems analysis and technical specification writing:
- Requirements discovery from codebase and stakeholders
- Systems thinking: interfaces, boundaries, dependencies
- Architectural analysis and tradeoff evaluation
- Clear, maintainable OpenSpec documentation

**Key Features**:
- Write access limited to `./openspec/` and `./docs/` only
- Encourages creation of Mermaid diagrams for visual clarity
- Documents decision rationale and tradeoffs
- Integrates with OpenSpec conventions

**Resources**:
- `README.md`, `AGENTS.md`, `openspec/AGENTS.md`
- `.kiro/rules/**/*.md` (project rules only)
- OpenSpec documentation via guide MCP

**Pre-trusted Tools**: Same as `guide` agent

## Usage with Kiro CLI

After installation, invoke agents using Kiro CLI:

```bash
# Use the guide agent
kiro-cli chat --agent guide

# Use the review agent
kiro-cli chat --agent guide-review

# Use the spec agent
kiro-cli chat --agent guide-spec
```

### Setting the Default Agent

To avoid specifying `--agent` every time, set `guide` as your default agent:

```bash
kiro-cli settings set chat.defaultAgent guide
```

This makes `guide` the default for all Kiro sessions. You can still override it per-session with `--agent` when needed. The structured workflow provided by `guide` works well as a default since it enforces disciplined development practices while allowing you to delegate to specialised agents (like `guide-review` or `guide-spec`) when needed.

### Switching Between Agents

You can switch agents mid-session or for specific tasks:

```bash
# Start with guide agent (if set as default)
kiro-cli chat

# In a new session, use review agent for code review
kiro-cli chat --agent guide-review

# In another session, use spec agent for writing specifications
kiro-cli chat --agent guide-spec
```

Alternatively, use the `delegate` or `use_subagent` tools within a session to invoke specialised agents without leaving your current context. This is useful when you need a quick review or spec update while working in the main `guide` workflow.

## Pre-trusted Tools

All agents pre-trust the following tool categories:
- **File operations**: `ls`, `read`, `fs_read`, `write`, `fs_write`
- **Execution**: `execute_bash`, `shell`
- **Delegation**: `delegate`, `subagent`
- **AWS**: `aws`
- **Search**: `glob`, `grep`
- **Utilities**: `report`, `introspect`, `knowledge`, `thinking`, `todo`
- **Web**: `web_fetch`, `web_search`
- **Code intelligence**: `code`
- **MCP servers**: `@git/*`, `@guide/*`, `@github/*`, `@context7/*`, `@sequentialthinking/*`, `@atlassian/*`

This pre-trust configuration eliminates permission prompts for these commonly-used and widely trusted tools.
