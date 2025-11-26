# ADR-006: Session Management Architecture

**Date:** 2025-11-26
**Status:** Accepted
**Context:** Core Architecture for mcp-guide v2

## Problem

The v1 architecture used a singleton SessionManager that caused issues with:
- Testing complexity (global state)
- Tight coupling between session state and config management
- Difficulty supporting concurrent operations on different projects
- Hidden global state making behavior unpredictable

The singleton was at the wrong level of abstraction - the config file is the true global concern, not the session state.

## Decision

Implement a two-tier architecture:
1. **ProjectConfigManager** (Singleton) - Manages ALL project configurations
2. **GuideSession** (Non-Singleton) - Runtime state for a specific project
3. **ContextVar** - Tracks current session per async task

## Architecture

### ProjectConfigManager (Singleton)

**Responsibility**: Manage all project configurations in a single YAML file

```python
class ProjectConfigManager:
    """Singleton manager for all project configurations.

    Manages a single YAML file containing all project configs.
    Thread-safe and async-safe with file locking.
    """

    _instance: Optional['ProjectConfigManager'] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.config_file = Path.home() / ".config" / "mcp-guide" / "config.yaml"
        self._file_lock = FileLock(self.config_file.with_suffix('.lock'))
        self._initialized = True

    def get_or_create_project_config(self, project_name: str) -> Project:
        """Get project config, creating with defaults if not exists.

        Returns immutable Project instance.
        Validates project name immediately.
        """

    def save_project_config(self, project: Project) -> None:
        """Save project config atomically with file locking."""

    def rename_project(self, old_name: str, new_name: str) -> None:
        """Rename a project, updating all references."""

    def list_projects(self) -> List[str]:
        """List all known project names."""

    def delete_project(self, project_name: str) -> None:
        """Delete a project configuration."""
```

**Key Characteristics:**
- Singleton pattern (one instance per process)
- Manages single YAML file with all projects
- File locking for atomic operations
- Returns immutable Project objects
- Validates project names immediately

### GuideSession (Non-Singleton)

**Responsibility**: Runtime state for a specific project

```python
@dataclass
class GuideSession:
    """Non-singleton session for a specific project.

    Each session represents runtime state for one project.
    Multiple sessions can coexist for different projects.
    """

    project_name: str
    config_manager: ProjectConfigManager
    _project: Optional[Project] = None
    state: SessionState = field(default_factory=SessionState)

    def __post_init__(self):
        """Validate project name immediately on creation."""
        if not self.project_name:
            raise ValueError("Project name cannot be empty")
        # Project config loaded lazily on first access

    @property
    def project(self) -> Project:
        """Get project config (lazy loaded)."""
        if self._project is None:
            self._project = self.config_manager.get_or_create_project_config(
                self.project_name
            )
        return self._project

    def update_config(self, updater: Callable[[Project], Project]) -> None:
        """Update config using functional pattern.

        Example:
            session.update_config(lambda p: p.with_category(category))
        """
        new_project = updater(self.project)
        self.config_manager.save_project_config(new_project)
        self._project = new_project

    def get_state(self) -> SessionState:
        """Get mutable runtime state."""
        return self.state
```

**Key Characteristics:**
- NOT a singleton - multiple instances can exist
- Lightweight and testable
- Eager name resolution, lazy config loading
- Holds reference to global ProjectConfigManager
- Immutable config, mutable state

### Immutable Project Model

**Responsibility**: Immutable configuration data

```python
@dataclass(frozen=True)
class Project:
    """Immutable project configuration.

    All modifications return new Project instances.
    """

    name: str
    categories: Dict[str, Category]
    collections: Dict[str, Collection]
    created_date: datetime
    modified_date: datetime

    def with_category(self, category: Category) -> 'Project':
        """Return new Project with added/updated category."""
        new_categories = {**self.categories, category.name: category}
        return replace(
            self,
            categories=new_categories,
            modified_date=datetime.now(timezone.utc)
        )

    def without_category(self, name: str) -> 'Project':
        """Return new Project with category removed."""
        new_categories = {k: v for k, v in self.categories.items() if k != name}
        return replace(
            self,
            categories=new_categories,
            modified_date=datetime.now(timezone.utc)
        )

    # Similar methods for collections, etc.
```

**Key Characteristics:**
- Frozen dataclass (immutable)
- Functional updates return new instances
- Serializable to/from YAML
- Pydantic validation

### ContextVar Integration

**Responsibility**: Track current session per async task

```python
from contextvars import ContextVar

# Global ContextVar
active_sessions: ContextVar[Dict[str, GuideSession]] = ContextVar(
    'active_sessions',
    default={}
)

def get_current_session(project_name: str) -> Optional[GuideSession]:
    """Get session for project from current context."""
    sessions = active_sessions.get()
    return sessions.get(project_name)

def set_current_session(session: GuideSession) -> None:
    """Register session in current context."""
    sessions = active_sessions.get().copy()
    sessions[session.project_name] = session
    active_sessions.set(sessions)

def remove_current_session(project_name: str) -> None:
    """Remove session from current context."""
    sessions = active_sessions.get().copy()
    sessions.pop(project_name, None)
    active_sessions.set(sessions)
```

**Key Characteristics:**
- Dict keyed by project name
- One session per project
- Isolated per async task
- Automatically propagates through async call chains

## Tool Integration

Tools access sessions via ContextVar:

```python
from fastmcp import Context

@mcp.tool()
async def guide_get_category(name: str, ctx: Context) -> Result[dict]:
    """Get category from current project."""
    # Get project name from somewhere (tool parameter, config, etc.)
    project_name = "current-project"  # TODO: determine from context

    session = get_current_session(project_name)
    if not session:
        return Result.failure("No active session for project", "session_error")

    project = session.project
    category = project.categories.get(name)

    if not category:
        return Result.failure(f"Category '{name}' not found", "not_found")

    return Result.ok(category.to_dict())
```

## Benefits

### Correct Singleton Scope
- Config file management is the true global concern
- Session state is per-project, not global
- Clear separation of concerns

### Testability
- Sessions can be created in isolation
- Config manager can be mocked
- No hidden global state

### Concurrency Support
- ContextVar provides task-local storage
- Multiple async tasks can work on different projects
- No race conditions between sessions

### Immutability
- Configuration changes are explicit
- Functional updates prevent accidental mutations
- Easy to reason about state changes

### Explicit Lifecycle
- Session creation is explicit
- Session scope is clear
- No magic global access

## Consequences

### Positive
- Clean architecture with proper separation
- Testable components
- Concurrent operations supported
- Immutable configs prevent bugs
- Explicit session management

### Negative
- More verbose than singleton access
- Need to pass session or use ContextVar
- Slightly more complex initialization

### Migration from v1
- Breaking change - no compatibility layer
- Clean slate approach
- Rewrite all session access code

## Implementation Notes

### File Locking
Use `filelock` package for portable file locking:
```python
from filelock import FileLock

with FileLock(config_file.with_suffix('.lock')):
    # Atomic read/write operations
```

### YAML Format
```yaml
projects:
  my-project:
    name: my-project
    created_date: 2025-11-26T00:00:00Z
    modified_date: 2025-11-26T00:00:00Z
    categories:
      guide:
        name: guide
        dir: guide/
        patterns: [guidelines]
    collections:
      default:
        name: default
        categories: [guide, lang, context]
```

### Error Handling
All operations return Result[T] for consistent error handling.

## Status

Accepted - to be implemented in Phase 3 after main-entry-point is complete.

## References

- Architecture Spec: `openspec/project.md`
- ADR-003: Result Pattern for Tool and Prompt Responses
- v1 Issues: Testing complexity, hidden state, tight coupling
