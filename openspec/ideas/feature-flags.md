# Idea: Feature Flags Configuration

**Status:** Incubating
**Date:** 2025-12-08
**Category:** Configuration Management

## Overview

Add feature flag support to the configuration system, enabling global and project-specific feature toggles with flexible value types.

## Motivation

- Enable/disable features without code changes
- Support gradual feature rollout
- Allow project-specific feature customization
- Provide feature configuration beyond simple boolean toggles

## Design

### Configuration Structure

#### Global Feature Flags

Located at the top level of the configuration file (applies to all projects):

```yaml
feature-flags:
  openspec-support: true
  workflow-category: workflows
  ext-support:
    ext-mappings: true
    ext-categories:
      - stories
      - tasks
  issue-tracking: "jira"
```

**Characteristics:**
- Optional configuration section
- Key-value mapping
- Values can be: boolean, string, list, or mapping (dict)
- Applies to all projects by default

#### Project Feature Flags

Located within individual project configuration:

```yaml
projects:
  my-project:
    project-flags:
      openspec-support: false      # Override global
      custom-feature: true          # Project-specific
      workflow-category: custom-workflows
```

**Characteristics:**
- Optional per-project section
- Same value types as global flags
- Overrides global feature flags
- Can define project-specific flags

### Value Types

Feature flags support multiple value types:

1. **Boolean** - Simple on/off toggle
   ```yaml
   openspec-support: true
   ```

2. **String** - Configuration value
   ```yaml
   workflow-category: workflows
   issue-tracking: "jira"
   ```

3. **List** - Multiple values
   ```yaml
   enabled-tools:
     - category
     - collection
     - content
   ```

4. **Mapping** - Nested configuration
   ```yaml
   ext-support:
     ext-mappings: true
     ext-categories:
       - stories
       - tasks
   ```

### Resolution Priority

When resolving a feature flag value:

1. **Project-specific flag** (highest priority)
2. **Global flag**
3. **None** (flag not defined)

## API Design

### Feature Class

Generic class to represent feature flag values:

```python
from typing import Generic, TypeVar, Union

T = TypeVar('T')

class Feature(Generic[T]):
    """Represents a feature flag value.

    Attributes:
        name: Feature flag name
        value: Feature flag value (boolean, string, list, or dict)
        source: Where the value came from ('global', 'project', or 'default')
    """
    name: str
    value: T
    source: str  # 'global' | 'project' | 'default'

    def is_enabled(self) -> bool:
        """Check if feature is enabled (for boolean flags)."""
        if isinstance(self.value, bool):
            return self.value
        return self.value is not None

    def as_bool(self) -> bool:
        """Get value as boolean."""
        ...

    def as_str(self) -> str:
        """Get value as string."""
        ...

    def as_list(self) -> list:
        """Get value as list."""
        ...

    def as_dict(self) -> dict:
        """Get value as dict."""
        ...
```

### API Function

```python
async def get_feature(
    flag_name: str,
    project_name: Optional[str] = None
) -> Feature[T] | None:
    """Get feature flag value.

    Args:
        flag_name: Name of the feature flag
        project_name: Optional project name (uses current project if None)

    Returns:
        Feature object with value, or None if flag not defined

    Resolution order:
        1. Project-specific flag (if project_name provided)
        2. Global flag
        3. None (not defined)
    """
    ...
```

### Usage Examples

```python
# Boolean feature
feature = await get_feature("openspec-support")
if feature and feature.is_enabled():
    # Feature is enabled
    ...

# String feature
workflow_cat = await get_feature("workflow-category")
if workflow_cat:
    category_name = workflow_cat.as_str()

# Complex feature
ext_support = await get_feature("ext-support")
if ext_support:
    config = ext_support.as_dict()
    if config.get("ext-mappings"):
        categories = config.get("ext-categories", [])
```

## Template Context Integration

Feature flags must be available in template contexts for instruction rendering:

```python
# In template context
context = {
    "project": project,
    "features": {
        "openspec_support": await get_feature("openspec-support"),
        "workflow_category": await get_feature("workflow-category"),
        # ... other features
    }
}
```

**Template usage:**
```jinja2
{% if features.openspec_support.is_enabled() %}
OpenSpec support is enabled.
Workflow category: {{ features.workflow_category.as_str() }}
{% endif %}
```

## Configuration Model Changes

### Global Configuration

```python
@dataclass
class GlobalConfig:
    docroot: str
    projects: dict[str, Project]
    feature_flags: Optional[dict[str, Any]] = None  # NEW
```

### Project Configuration

```python
@dataclass
class Project:
    name: str
    categories: list[Category]
    collections: list[Collection]
    project_flags: Optional[dict[str, Any]] = None  # NEW
```

## Implementation Considerations

### Phase 1: Data Model
- Add `feature_flags` to global config
- Add `project_flags` to project config
- Update YAML serialization/deserialization
- Add validation

### Phase 2: Feature API
- Implement `Feature[T]` generic class
- Implement `get_feature()` function
- Add resolution logic (project → global → None)
- Add type conversion methods

### Phase 3: Template Integration
- Make features available in template context
- Add helper functions for common patterns
- Document template usage

### Phase 4: Built-in Features
- Define standard feature flags
- Document feature flag conventions
- Provide examples

## Use Cases

### 1. OpenSpec Integration
```yaml
feature-flags:
  openspec-support: true
  openspec-validation: auto
```

### 2. Workflow Customization
```yaml
feature-flags:
  workflow-category: workflows

projects:
  simple-project:
    project-flags:
      workflow-category: simple-workflow
```

### 3. Tool Enablement
```yaml
feature-flags:
  enabled-tools:
    - category
    - collection
    - content

projects:
  restricted-project:
    project-flags:
      enabled-tools:
        - category  # Only category tools
```

### 4. External Integrations
```yaml
feature-flags:
  issue-tracking: "jira"
  ci-integration:
    provider: github-actions
    auto-deploy: true
```

## Benefits

- **Flexibility** - Enable/disable features without code changes
- **Granularity** - Global and project-specific control
- **Type Safety** - Generic Feature[T] class with type conversion
- **Extensibility** - Support for complex configuration structures
- **Template Integration** - Available in instruction templates

## Open Questions

1. **Validation** - How to validate feature flag values?
2. **Defaults** - Should features have default values?
3. **Discovery** - How to list available feature flags?
4. **Documentation** - Where to document standard feature flags?
5. **Migration** - How to handle deprecated feature flags?
6. **Caching** - Should feature values be cached?
7. **Hot Reload** - Should feature changes take effect immediately?

## Related

- Configuration management system
- Template context system
- Project configuration model
- User-defined workflows (uses workflow-category flag)

## Next Steps

When this moves to proposal:
- Define exact configuration schema
- Specify Feature[T] class implementation
- Design validation rules
- Create standard feature flag registry
- Plan template integration
- Document usage patterns
