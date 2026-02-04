# Refactor Utils Package

## Problem

The `utils/` package has become a catch-all for unrelated functionality, making it difficult to:
- Understand module organization and dependencies
- Locate relevant code for specific features
- Maintain clear architectural boundaries
- Identify dead or orphaned code

## Solution

Reorganize utils modules into cohesive, functionally-grouped packages:

### 1. Content Package (`content/`)

**Purpose**: Content gathering, formatting, and file discovery

**Modules to move**:
- `content_common.py` → `content/gathering.py` - Expression parsing, orchestration
- `content_utils.py` → `content/utils.py` - File reading, instruction extraction
- `content_formatter_base.py` → `content/formatters/base.py`
- `content_formatter_mime.py` → `content/formatters/mime.py`
- `content_formatter_plain.py` → `content/formatters/plain.py`
- `formatter_selection.py` → `content/formatters/selection.py`

**Rationale**: These modules form the content pipeline used by MCP tools

**Note**: `file_discovery.py` moved to `discovery/` package instead

### 2. Render Package (existing, expand)

**Purpose**: Template rendering, context management, and partials

**Modules to move into `render/`**:
- `template_renderer.py` → `render/renderer.py` - Core rendering logic
- `template_context.py` → `render/context.py` - Context data structures
- `template_context_cache.py` → `render/cache.py` - Context caching
- `template_functions.py` → `render/functions.py` - Template helper functions
- `template_partials.py` → `render/partials.py` - Partial loading
- `frontmatter.py` → `render/frontmatter.py` - Frontmatter parsing
- `frontmatter_types.py` → `render/frontmatter_types.py` - Type definitions

**Rationale**: These modules are used by the render package and form a cohesive rendering subsystem

### 3. Discovery Package (`discovery/`)

**Purpose**: Pattern matching and file/command discovery

**Modules to move**:
- `pattern_matching.py` → `discovery/patterns.py` - Pattern matching utilities
- `command_discovery.py` → `discovery/commands.py` - Command discovery
- `file_discovery.py` → `discovery/files.py` - File discovery by patterns

**Rationale**: All discovery functionality unified in one package

**Note**: `file_discovery.py` moved here from content package for better cohesion

### 4. Feature Flags Package (existing)

**Modules to move**:
- `flag_utils.py` → `feature_flags/utils.py` - Flag resolution utilities

**Rationale**: Already have `feature_flags/` package, this belongs there

### 5. Commands Package (`commands/`)

**Purpose**: Command-related utilities

**Modules to move**:
- `command_formatting.py` → `commands/formatting.py`
- `command_security.py` → `commands/security.py`

**Rationale**: Command utilities are distinct from general utils and warrant their own package

### 6. Remaining in Utils

**Keep in `utils/`** (truly general utilities):
- `client_path.py` - Client path resolution
- `duration_formatter.py` - Duration formatting
- `project_hash.py` - Project hash calculation

## Benefits

1. **Clarity**: Clear functional grouping makes code easier to find
2. **Maintainability**: Related code changes together
3. **Encapsulation**: Better module boundaries
4. **Discoverability**: New developers can navigate more easily
5. **Dead code detection**: Easier to identify unused modules

## Implementation Strategy

1. Create new package directories with `__init__.py`
2. Move modules and update imports
3. Update all import statements across codebase
4. Run tests to verify no breakage
5. Update documentation

## Risks

- Large number of import changes across codebase
- Potential for merge conflicts if done during active development
- Need to update any external documentation

## Alternatives Considered

1. **Leave as-is**: Continue with cluttered utils package - Rejected: reduces maintainability
2. **Partial refactor**: Only move most egregious cases - Rejected: doesn't solve the problem
3. **Create template/ package**: Keep separate from render/ - Rejected: better cohesion in render/

## Open Questions

None - all structural decisions resolved:
1. ✅ Template modules merge with render/ package
2. ✅ File discovery moves to discovery/ package with patterns
3. ✅ Command modules get their own package
