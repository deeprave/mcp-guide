# Tasks: Complete OpenSpec Schema Caching

## Status: 📋 PLANNED

## Implementation Tasks

### 1. Add schema response handler to OpenSpecTask
**File**: `src/mcp_guide/client_context/openspec_task.py`

- [ ] Add `_schemas` state variable to `__init__`
- [ ] Add handler for `.openspec-schemas.json` in `handle_event()`
- [ ] Extract schema names from JSON response
- [ ] Cache schemas in task manager
- [ ] Update feature flag object with schemas
- [ ] Add `get_schemas()` getter method

### 2. Update template context with schemas
**File**: `src/mcp_guide/utils/template_context_cache.py`

- [ ] Add `schemas` field to openspec context object
- [ ] Use `get_schemas()` from OpenSpecTask subscriber
- [ ] Default to empty list when not available

### 3. Add schema field to workflow state
**File**: `src/mcp_guide/workflow/schema.py`

- [ ] Add optional `schema` field to WorkflowState dataclass
- [ ] Update `from_yaml()` to parse schema field
- [ ] Update `to_yaml()` to serialize schema field

### 4. Add tests for schema caching
**File**: `tests/test_openspec_task.py`

- [ ] Test handling schemas JSON response
- [ ] Verify schemas cached in task state
- [ ] Verify schemas cached in task manager
- [ ] Verify feature flag updated with schemas

### 5. Add tests for workflow schema field
**File**: `tests/unit/test_workflow_schema.py`

- [ ] Test WorkflowState with schema field
- [ ] Test schema serialization to YAML
- [ ] Test schema parsing from YAML
- [ ] Test schema field is optional

## Verification

- [ ] Run `:openspec/schemas` command
- [ ] Verify schemas in feature flag object
- [ ] Verify `openspec.schemas` in template context
- [ ] Add schema to `.guide.yaml` and verify persistence
- [ ] All tests pass
