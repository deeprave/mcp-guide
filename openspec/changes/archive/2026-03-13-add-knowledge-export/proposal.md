# Change: Add export_content tool for knowledge indexing

## Why
Agents normally consume content via `get_content`, which dumps the full document text into the context window. Kiro and kiro-cli support a "knowledge" indexing mechanism that allows documents to be semantically queried using a tiny fraction of the context window. This change adds `export_content` — identical to `get_content` but with an export path argument — which returns the **rendered** content to the agent along with an instruction to write it to the specified path for knowledge indexing.

The MCP server cannot write to the agent's filesystem directly; the agent performs the write based on the instruction in the response.

## What Changes

### 1. Path Configuration Flags (Prerequisite)
Two new feature/project flags for configurable output paths:

**`path-documents`** - Working documents output path
- Default: `.todo/`
- Purpose: Where reviews, implementation plans, and working documents are stored
- Scope: Feature and Project (user preference)
- Auto-added to `allowed_write_paths`
- Available in templates as `{{path.documents}}`

**`path-export`** - Export document output path
- Default: Agent-specific (see table below)
- Purpose: Where knowledge/indexing documents are exported
- Scope: Feature and Project (can override agent default)
- Auto-added to `allowed_write_paths`
- Available in templates as `{{path.export}}`

**Agent-specific defaults for `path-export`:**
| Agent | Default Path |
|-------|-------------|
| kiro, q-dev | `.kiro/knowledge/` |
| claude, claude-code | `.claude/knowledge/` |
| cursor, cursor-agent | `.cursor/knowledge/` |
| copilot | `.github/instructions/knowledge/` |
| gemini | `.gemini/knowledge/` |
| codex | `.codex/knowledge/` |
| goose, block-goose-cli | `.goose/skills/` |
| unknown | `.knowledge/` |

**Path validation:**
- Both paths validated using existing security functions (same as `workflow-file`)
- Must be relative paths within project root
- Cannot escape project root (no `../`)
- Invalid paths fall back to defaults

**Agent detection:**
- If agent not detected when flag is resolved, prompt agent to run detection (same pattern as `:status` and `:review` commands)
- Once any tool is called, agent info is automatically cached
- Agent switching changes `path-export` default (intentional behavior)
- Project flag can lock path to specific value regardless of agent

### 2. export_content Tool
New tool that leverages existing content infrastructure:

**Interface:**
- `expression` (required): Same as `get_content` - category/collection expression
- `pattern` (optional): Same as `get_content` - glob pattern filter
- `path` (optional): Export path; defaults to `path-export` flag + document name
- `force` (default `False`): Allow overwriting existing files

**Implementation:**
- Reuses `internal_get_content()` for content gathering, rendering, and formatting
- Respects `content-format` flag (None/plain/mime) - same as `get_content`
- Validates `path` against `allowed_write_paths` using existing security functions
- Returns rendered content with instruction directing agent to write to `path`
- If `force=False` and file exists, instruction indicates create-only
- If `force=True`, instruction permits overwrite

**Path behavior:**
- If `path` provided: validate against `allowed_write_paths`
- If `path` omitted: use `path-export` flag + append document name

### 3. Template Updates
Update templates that hardcode paths:
- `workflow/review.mustache`: Replace `.todo/` with `{{path.documents}}`
- Any other templates referencing hardcoded paths

### 4. Configuration Changes
- Remove `.kiro/knowledge/` from `DEFAULT_ALLOWED_WRITE_PATHS` (now dynamic via flags)
- Auto-add resolved `path-documents` and `path-export` to `allowed_write_paths`
- Deduplicate paths in serialization

## Impact

### Affected Specs
- **New**: `knowledge-export` (this change)
- **Modified**: `feature-flags` (add path-documents, path-export)
- **Modified**: `template-context` (add path.* namespace)
- **Modified**: `project-config` (auto-addition of flag paths to allowed_write_paths)
- **Cross-references**: `content-tools`, `content-formatting`, `content-processing`

### Affected Code
- `src/mcp_guide/feature_flags/constants.py` - Add flag definitions
- `src/mcp_guide/feature_flags/validators.py` - Add path validators
- `src/mcp_guide/render/context.py` - Add path.* to template context
- `src/mcp_guide/session.py` - Auto-add flag paths to allowed_write_paths
- `src/mcp_guide/tools/tool_content.py` - Add export_content tool
- `src/mcp_guide/templates/_commands/workflow/review.mustache` - Use {{path.documents}}

### Backward Compatibility
- Non-breaking: `get_content` unchanged
- Existing configs with explicit `allowed_write_paths` work unchanged
- Existing hardcoded `.todo/` paths in templates replaced with dynamic flag
- Agent-aware defaults provide better out-of-box experience

### Security
- Uses existing path validation functions (same as workflow-file)
- Paths restricted to project root
- No new security surface - leverages existing infrastructure
