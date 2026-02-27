# Enhance Guide Prompt Parsing

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

Currently, command flags in the guide prompt system only support `--flag=value` syntax. Users naturally expect `--flag value` (space-separated) syntax to work as well, which is standard in most CLI tools. This creates a poor UX where `--tracking GUIDE-177` is parsed as a boolean flag plus a positional argument instead of a key-value pair.

This enhancement improves usability by supporting both syntaxes while maintaining backward compatibility.

## What Changes

- **Frontmatter Schema**: Add `argrequired` top-level field to declare flags that require values
- **Command Parser**: Enhance `parse_command_arguments()` to consume next argument when flag is in `argrequired` list
- **Template Updates**: Update affected command templates to include `argrequired` declarations
- **Error Handling**: Add validation to error when required value is missing

### Affected Components

1. `src/mcp_guide/prompts/command_parser.py` - Parser logic
2. `src/mcp_guide/templates/_commands/workflow/issue.mustache` - `--issue`, `--description`, `--tracking`, `--queue`
3. `src/mcp_guide/templates/_commands/create/category.mustache` - `--dir`, `--patterns`, `--description`
4. `src/mcp_guide/templates/_commands/create/collection.mustache` - `--description`

## Technical Approach

### Frontmatter Format

```yaml
argrequired:
  - tracking
  - issue
  - description
```

### Parser Behavior

1. Parse frontmatter to extract `kwargs.argrequired` list
2. When processing `--flag`:
   - If `flag` in `argrequired` and no `=` present:
     - Consume next argument as value
     - Error if next argument is missing or starts with `-`
   - Otherwise: use current behavior (boolean flag)
3. `--flag=value` syntax continues to work unchanged

### Example Transformations

**Before:**
- `--tracking GUIDE-177` → `kwargs["tracking"] = True`, `args = ["GUIDE-177"]`

**After:**
- `--tracking GUIDE-177` → `kwargs["tracking"] = "GUIDE-177"`, `args = []`
- `--tracking=GUIDE-177` → `kwargs["tracking"] = "GUIDE-177"`, `args = []` (unchanged)
- `--tracking` → Error: "Flag --tracking requires a value"

## Success Criteria

1. Both `--flag value` and `--flag=value` syntaxes work for declared flags
2. Error messages when required values are missing
3. Backward compatibility: commands without `kwargs.argrequired` work unchanged
4. All existing tests pass
5. New tests cover both syntaxes and error cases
