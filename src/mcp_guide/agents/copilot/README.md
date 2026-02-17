# GitHub Copilot Agent Configurations

Specialised agent configurations for [GitHub Copilot](https://github.com/features/copilot).

## Installation

```bash
# Install to home directory
guide-agent-install copilot ~

# Install to current directory
guide-agent-install copilot .

# Install to specific directory
guide-agent-install copilot /path/to/project
```

Installs agents to `<dirname>/.github/agents/`.

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

## Usage with GitHub Copilot

After installation, agents are available in VS Code's Copilot Chat:

1. Open GitHub Copilot Chat (sidebar or inline)
2. Click the agent picker dropdown (shows active agent, usually `@workspace`)
3. Select your custom agent from the list (e.g., "Guide", "Guide Review", "Guide Spec")
4. Type your message

**Note**: Custom agents are selected from the dropdown, not invoked with `@` symbol. The `@` symbol is reserved for built-in agents like `@workspace`, `@terminal`, and `@vscode`.

### Agent Structure

Each agent is defined in an `.agent.md` file with:
- YAML frontmatter (description, name, optional handoffs)
- Markdown body with detailed instructions
- Examples showing expected behaviour
- Clear rules and constraints

GitHub Copilot reads these agent files to understand when and how to apply specific workflows and constraints.
