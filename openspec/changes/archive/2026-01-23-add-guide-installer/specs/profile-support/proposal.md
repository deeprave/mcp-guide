# Profile Support

## Overview
Add composable profile system to incrementally configure projects by applying minimal, additive profiles for language, tracking system, workflow methodology, and compliance requirements.

## Problem Statement
Users need quick, standardized ways to configure projects for different languages, tracking systems, workflows, and compliance requirements without manually creating categories and collections each time.

## Proposed Solution
Implement a composable profile system where:
- Profiles are minimal YAML files defining categories and collections
- Profiles are additive (never remove or replace existing config)
- Multiple profiles can be applied to compose complex configurations
- Profiles are organized by dimension: language, tracking, workflow, compliance

## Profile Dimensions

### Language Profiles
- `python` - Python source patterns, test conventions
- `rust` - Cargo structure, Rust conventions
- `java` - Maven/Gradle structure, Java conventions
- `typescript` - Node.js structure, TS/JS conventions
- `go` - Go module structure, conventions

### Tracking System Profiles
- `jira` - Jira-specific categories (issues, epics, stories)
- `github` - GitHub issues, PRs, discussions
- `linear` - Linear issue tracking
- `youtrack` - YouTrack conventions
- `asana` - Asana task tracking

### Workflow Profiles
- `tdd` - Test-driven development structure
- `bdd` - Behavior-driven development (features, scenarios)
- `develop-test` - Traditional develop-then-test workflow

### Compliance Profiles
- `sox` - SOX compliance documentation
- `hipaa` - HIPAA compliance requirements
- `gdpr` - GDPR compliance tracking
- `iso27001` - ISO 27001 security standards

## API Design

### New Tool: `use_project_profile`

```python
# Apply single profile to current project
use_project_profile(profile="python")

# Apply multiple profiles to compose configuration
use_project_profile(profile="python")
use_project_profile(profile="jira")
use_project_profile(profile="tdd")
```

**Behavior:**
- Applies profile to current project only (no cross-project operations)
- Adds categories/collections (never removes)
- Skips duplicates (by category/collection name)
- Updates project metadata to track applied profiles
- Idempotent - applying same profile twice has no effect

## Profile Structure

Profiles are stored in `templates/_profiles/*.yaml`:

```yaml
# python.yaml - minimal Python-specific additions
categories:
  - name: api-docs
    dir: docs/api/
    patterns: []
    description: API documentation

collections:
  - name: python-docs
    description: Python documentation
    categories: [api-docs]
```

**Key Points:**
- Profiles contain only categories and collections
- Directory paths must be relative and end with `/`
- Patterns array can be empty (templates discovered separately)
- Files starting with `_` (like `_default.yaml`) are excluded from discovery

## Implementation Approach

1. Create Profile model for loading/validating YAML
2. Implement profile discovery in templates/_profiles/
3. Add `profile_project` tool to apply profiles
4. Track applied profiles in project metadata
5. Create profile YAML files for all dimensions
6. Add profile listing and inspection tools

## Success Criteria
- Profiles are composable and additive
- Multiple profiles can be applied without conflicts
- Profile application is idempotent
- All profile dimensions covered (language, tracking, workflow, compliance)
- Documentation complete

## Dependencies
- Requires completed installer implementation (Phases 1-5)
- No new external dependencies needed

## Design Principles
1. **Minimal** - Each profile adds only what's necessary
2. **Additive** - Profiles never remove or replace
3. **Composable** - Multiple profiles work together
4. **Focused** - One concern per profile
5. **Idempotent** - Safe to apply multiple times
