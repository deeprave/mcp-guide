# Project Context

## Purpose
MCP Guide v2 is a clean reimplementation of mcp-server-guide with correct architectural patterns. It provides a Model Context Protocol (MCP) server for managing project documentation, categories, collections, and prompts with proper session management and concurrent project support.

## Tech Stack
- **Python 3.13+** - Modern Python with latest features
- **FastMCP** - MCP server framework with Context support
- **Pydantic** - Data validation and settings management
- **asyncio** - Async/await for concurrent operations
- **contextvars** - Context-aware concurrency for multi-project support
- **Chevron** - Mustache template rendering
- **OpenSpec CLI** - Change proposal and spec management

## Project Conventions

### Code Style
- **Minimal implementations** - YAGNI principle, smallest code that solves the problem
- **Type hints** - Full type annotations for all functions
- **Immutability first** - Configuration objects are immutable
- **Explicit over implicit** - No hidden global state, clear lifetimes

### Architecture Patterns

#### Core Principles
1. **Immutability First** - Configuration objects are immutable (use functional updates)
2. **Explicit Over Implicit** - Session lifetime and scope are explicit
3. **Correct Singleton Scope** - Only truly global concerns are singletons
4. **Context-Aware Concurrency** - Support concurrent operations on different projects via ContextVar
5. **YAGNI** - Smallest possible implementation that solves the problem

#### Key Components
- **ProjectConfigManager** (Singleton) - Manages ALL project configs in single file
- **GuideSession** (Non-Singleton) - Runtime state for specific project
- **ContextVar** - Tracks current session per async task (`Dict[str, GuideSession]`)
- **Result[T]** - Error handling pattern for tool responses
- **TemplateContextCache** - Hierarchical context for template rendering
- **FeatureFlags** - Global and project-level feature flags with resolution hierarchy
- **TaskManager** - Background tasks for OpenSpec monitoring and workflow tracking
- **WorkflowState** - Phase-based workflow state (.guide.yaml)

#### Session Management
- Session name = project name (one session per project)
- Sessions stored in ContextVar for async task isolation
- Config loaded/created on session initialization
- Project name resolved immediately (no lazy loading of name)

### Testing Strategy
- **TDD** - Test-Driven Development with red-green-refactor cycles
- **Smallest possible steps** - Incremental test-first approach
- **Unit tests** - Components in isolation with mocked dependencies
- **Integration tests** - End-to-end session lifecycle and tool execution
- **Property tests** - Immutability guarantees, concurrent safety
- **Coverage target** - ≥ 90%

### Git Workflow
- **Conventional commits** - `type(scope): subject` format
- **Feature branches** - One branch per OpenSpec change
- **Incremental commits** - Small, focused commits per task
- **No migration path** - Clean break from v1, no backward compatibility

## Domain Context

### MCP Protocol
- Tools receive FastMCP `Context` parameter
- Prompts receive `ctx: Optional[Context]` (investigate when None)
- Resources provide read-only access to documentation
- All operations are async

### Configuration Management
- Single YAML file stores all project configurations
- Immutable Project objects returned from config manager
- Functional updates: `project.with_category(category)` returns new Project
- Atomic saves using lock file pattern for portability
- Feature flags stored in global config and per-project overrides
- Workflow state tracked in .guide.yaml (phase, issue, queue)

### Template System
- Mustache/Chevron templates for dynamic content generation
- Hierarchical context with ChainMap (agent → workflow → formatting → openspec)
- Template discovery from ~/.config/mcp-guide/docs/ directory
- Frontmatter-based requirements checking (requires-openspec, requires-workflow)
- Command templates for agent instructions

### OpenSpec Integration
- Change proposals tracked in openspec/changes/
- Specs define capabilities in openspec/specs/
- CLI integration via OpenSpecTask background monitoring
- Template context provides openspec availability and version
- Agent instructions for creating and managing changes

### Workflow System
- Phase-based workflow: discussion → planning → implementation → check → review
- State tracked in .guide.yaml (phase, issue, queue)
- WorkflowMonitorTask detects state changes
- Template context provides workflow state to agent instructions
- Automatic phase transitions based on completion

### Client-Server Filesystem Interaction
- Agent sends file content via send_file_content tool
- Agent sends directory listings via send_directory_listing tool
- Server caches client filesystem state for session duration
- Security: Client validates paths against allowed_read_paths
- Enables OpenSpec change discovery and validation

### Session Lifecycle
1. **Creation** - Session created with project name, config loaded/created
2. **Usage** - Tools access session via ContextVar, get immutable config
3. **Updates** - Config changes create new Project instance and persist
4. **Destruction** - Session removed from ContextVar, no global state remains

## Important Constraints

### Technical
- Must support concurrent async operations on different projects
- Config file must be portable across filesystems (use lock files)
- Session names must be unique (enforced by ContextVar dict)
- All configuration changes must be atomic

### Design
- No hidden global state beyond ProjectConfigManager singleton
- No lazy loading of project names (resolve immediately)
- No multiple sessions per project (session name = project name)
- No migration path from v1 (clean slate)

## External Dependencies
- **FastMCP** - MCP server framework
- **Pydantic** - Data validation
- **PyYAML** - Configuration file format
- **Chevron** - Mustache template rendering
- **pytest** - Testing framework
- **mypy** - Static type checking
- **OpenSpec CLI** - Change and spec management (external tool)
