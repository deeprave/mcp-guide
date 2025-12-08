# Change: Make Pydantic Models Resilient to Extra Fields

**JIRA:** GUIDE-117

## Why

The current Pydantic models (`Project`, `Category`, `Collection`) fail when encountering extra fields in hand-edited YAML configs, causing `ValueError` exceptions. This makes the system fragile and prevents backward compatibility when fields are removed from models.

## What Changes

This change improves the resilience of the configuration system by making Pydantic models tolerant of extra fields. We'll add `model_config = ConfigDict(extra='ignore')` to the three core models (Project, Category, Collection), allowing them to silently ignore any fields in the YAML that aren't defined in the model schema. This prevents errors when users hand-edit configs with typos or when loading legacy configs that contain deprecated fields. Additionally, we'll remove the redundant `"project"` key from the `format_project_data()` function output, which currently duplicates the project name that's already present as the dictionary key in list operations.

The implementation follows a TDD approach with unit tests verifying that each model correctly ignores extra fields, and integration tests confirming that config loading works with real YAML files containing extra fields. All existing tests must continue to pass, ensuring no regression in current functionality.

- Configure `Project`, `Category`, and `Collection` models with `extra='ignore'` to silently ignore unrecognized fields
- Remove redundant `"project"` key from `format_project_data()` output (currently duplicates information already in parent object key)

## Impact

- **Affected specs**: `models`
- **Affected code**:
  - `src/mcp_guide/models.py` - Add `ConfigDict(extra='ignore')` to 3 models, remove redundant key from formatter
  - Tests that verify model behavior with extra fields
- **Breaking change**: Removing `"project"` key from output may affect consumers expecting that field
- **Benefits**: Improved resilience to config errors, backward compatibility for deprecated fields

## Acceptance Criteria

- [ ] All three models (Project, Category, Collection) have `model_config = ConfigDict(extra='ignore')`
- [ ] Unit tests verify each model ignores extra fields without error
- [ ] Integration test verifies config loading works with YAML containing extra fields
- [ ] `format_project_data()` no longer returns redundant `"project"` key
- [ ] All existing 641 tests pass
- [ ] Code coverage remains ≥90%
- [ ] Manual test confirms `gv2_list_projects` works with hand-edited config
- [ ] No regression in tool behavior (get_current_project, list_projects, etc.)
