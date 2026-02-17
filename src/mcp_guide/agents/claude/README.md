# Claude Code Agent Configurations

Specialised agent configurations for [Claude Code](https://code.claude.com/).

## Installation

```bash
# Install to home directory
guide-agent-install claude ~

# Install to current directory
guide-agent-install claude .

# Install to specific directory
guide-agent-install claude /path/to/project
```

Installs agents to `<dirname>/.claude/agents/`.

## Available Agents

### guide
**Purpose**: Structured development workflow with phase-based progression

Enforces a disciplined development cycle through five distinct phases with explicit consent requirements for implementation and review.

**Key Features**:
- Tracks progress via `.guide.yaml` file
- Requires explicit consent for implementation and review phases
- Prevents code changes during discussion/planning phases
- Integrates with OpenSpec for specifications

---

### guide-review
**Purpose**: Code review focusing on correctness, security, and consistency

Performs thorough code reviews by comparing working tree changes against HEAD, categorising issues by severity.

**Key Features**:
- Compares changes against existing codebase patterns
- Categorises issues by severity (Critical/Warning/Notes)
- Respects project conventions rather than imposing external standards
- Provides specific file/line references and concrete fixes

---

### guide-spec
**Purpose**: Requirements gathering and OpenSpec specification authoring

Specialises in systems analysis and technical specification writing with focus on clarity and maintainability.

**Key Features**:
- Write access limited to `./openspec/` and `./docs/` only
- Encourages creation of Mermaid diagrams for visual clarity
- Documents decision rationale and tradeoffs
- Integrates with OpenSpec conventions

## Usage with Claude Code

After installation, agents are available in the `.claude/agents/` directory. Claude Code automatically discovers and uses agents based on their descriptions and the current task context.

### Agent Structure

Each agent is a markdown file with:
- Clear purpose statement
- Key features and capabilities
- Usage guidelines and constraints
- Integration points with project structure

Claude Code reads these agent files to understand when and how to apply specific workflows and constraints.
