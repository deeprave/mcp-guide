# Profile Support - Tasks

## Status: 📋 PLANNED

## Implementation Tasks

### 1. Profile Discovery and Loading
**Module:** `src/mcp_guide/models/profile.py` (new)

- [ ] Create Profile dataclass
- [ ] Implement profile file discovery in templates/_profiles/
- [ ] Load and parse profile YAML
- [ ] Validate profile structure (categories, collections only)
- [ ] Handle missing profile errors

### 2. Profile Application Logic
**Module:** `src/mcp_guide/tools/tool_project.py`

- [x] Create `use_project_profile` tool
- [x] Load profile configuration
- [x] Merge profile categories into current project (skip duplicates)
- [x] Merge profile collections into current project (skip duplicates)
- [x] Track applied profiles in project metadata
- [x] Prevent duplicate application

### 3. Project Metadata Enhancement
**Module:** `src/mcp_guide/models.py`

- [x] Add `applied_profiles` list to project metadata
- [x] Track profile application order
- [x] Display applied profiles in project info

### 4. Profile Templates
**Files:** `templates/_profiles/*.yaml`

Create minimal, focused profiles:

**Language:**
- [x] `_default.yaml` - base structure (docs, notes)
- [x] `python.yaml` - Python-specific
- [x] `rust.yaml` - Rust-specific
- [ ] `java.yaml` - Java-specific
- [ ] `typescript.yaml` - TypeScript-specific
- [ ] `go.yaml` - Go-specific

**Tracking:**
- [x] `jira.yaml` - Jira tracking
- [x] `github.yaml` - GitHub tracking
- [ ] `linear.yaml` - Linear tracking
- [ ] `youtrack.yaml` - YouTrack tracking
- [ ] `asana.yaml` - Asana tracking

**Workflow:**
- [x] `tdd.yaml` - TDD structure
- [ ] `bdd.yaml` - BDD structure
- [ ] `develop-test.yaml` - Traditional workflow

**Compliance:**
- [ ] `sox.yaml` - SOX compliance
- [ ] `hipaa.yaml` - HIPAA compliance
- [ ] `gdpr.yaml` - GDPR compliance
- [ ] `iso27001.yaml` - ISO 27001

**Note:** Profiles only define categories/collections. Templates already exist in the regular template directories and are discovered via category patterns.

### 5. CLI Integration
**Module:** `src/mcp_guide/tools/tool_project.py`

- [x] `use_project_profile(profile="python")` - apply profile
- [x] `list_profiles()` - list available profiles
- [x] `show_profile(profile="python")` - show profile details
- [x] Show applied profiles in `get_project(verbose=True)`

### 6. Documentation
- [ ] Document profile system concept
- [ ] Document profile composition
- [ ] Document creating custom profiles
- [ ] Provide examples for common combinations

## Testing Strategy

### Unit Tests
- [x] Profile loading and parsing
- [x] Profile validation (only categories/collections allowed)
- [x] Duplicate detection and skipping
- [x] Profile metadata tracking

### Integration Tests
- [x] Apply single profile
- [x] Apply multiple profiles
- [x] Apply same profile twice (idempotent)
- [x] Invalid profile name handling

## Success Criteria
- [x] All unit tests pass
- [x] All integration tests pass
- [x] Profiles are composable and additive
- [x] No breaking changes to existing projects
- [ ] Documentation complete

## Additional Implementation Details

### Category Directory Validation
- Added `__post_init__` to `Category` class to ensure `dir` always ends with `/`
- Directory paths are relative and automatically normalized

### Profile Discovery
- Profiles starting with `_` are excluded from `discover_profiles()`
- Allows for internal/base profiles like `_default.yaml`
