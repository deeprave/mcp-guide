# Implementation Tasks

## Phase 1: Unify Frontmatter Processing

### 1.1 Create process_frontmatter() function
- [x] 1.1.1 Add `process_frontmatter()` to `render/frontmatter.py`
  - Combines: parse + requirements check + instruction/description rendering
  - Returns: `Optional[ProcessedFrontmatter]` (None if filtered by requires-*)
  - Parameters: content (str), requirements_context (dict), render_context (Optional[TemplateContext])
- [x] 1.1.2 Add `ProcessedFrontmatter` dataclass
  - Fields: frontmatter (Frontmatter), content (str), frontmatter_length (int), content_length (int)
- [x] 1.1.3 Write tests for `process_frontmatter()`
  - Test parse + requirements check
  - Test instruction/description rendering
  - Test filtering (returns None when requires-* not met)

### 1.2 Replace usage in render/template.py
- [x] 1.2.1 Replace lines 43-87 with `process_frontmatter()` call
- [x] 1.2.2 Update tests to verify behavior unchanged

### 1.3 Replace usage in render/renderer.py
- [x] 1.3.1 Replace lines 160-172 with `process_frontmatter()` call for partials
- [x] 1.3.2 Update tests to verify behavior unchanged

### 1.4 Replace usage in render/partials.py
- [x] 1.4.1 Replace lines 137-145 with `process_frontmatter()` call
- [x] 1.4.2 Update tests to verify behavior unchanged

### 1.5 Replace usage in discovery/commands.py
- [x] 1.5.1 Replace lines 118-135 with `process_frontmatter()` call
- [x] 1.5.2 Update tests to verify behavior unchanged

### 1.6 Replace usage in content/utils.py
- [x] 1.6.1 Replace lines 217-226 with `process_frontmatter()` call
- [x] 1.6.2 Update tests to verify behavior unchanged

### 1.7 Validation
- [x] 1.7.1 Run full test suite - all tests pass
- [x] 1.7.2 Run ruff and mypy - no issues
- [x] 1.7.3 Manual testing of commands and content retrieval

## Phase 2: Unify File Processing

### 2.1 Create process_file() function
- [x] 2.1.1 Add `process_file()` to `render/frontmatter.py`
  - Single entry point for non-template files
  - Uses `process_frontmatter()` internally
  - Returns: `Optional[ProcessedFrontmatter]`
  - Parameters: file_info (FileInfo), requirements_context (dict), template_context (Optional[TemplateContext])
- [x] 2.1.2 Write tests for `process_file()`
  - Test non-template files
  - Test requirements filtering

### 2.2 Simplify render/template.py
- [x] 2.2.1 Evaluated - no changes needed, serves distinct purpose
- [x] 2.2.2 Fixed context building bug
- [x] 2.2.3 Updated tests

### 2.3 Simplify content/utils.py
- [x] 2.3.1 Replace non-template processing with `process_file()` call
- [x] 2.3.2 Remove duplicate processing logic
- [x] 2.3.3 Update tests

### 2.4 Simplify discovery/commands.py
- [x] 2.4.1 Already using unified frontmatter parsing from Phase 1
- [x] 2.4.2 No further changes needed
- [x] 2.4.3 Tests passing

### 2.5 Validation
- [x] 2.5.1 Run full test suite - all 1615 tests pass
- [x] 2.5.2 Run ruff and mypy - no issues
- [x] 2.5.3 Manual testing of all affected features
- [x] 2.5.4 Performance check - no regressions

## Phase 3: Documentation and Cleanup

### 3.1 Update documentation
- [x] 3.1.1 Update render/README.md with new API
- [x] 3.1.2 Add docstrings to new functions
- [x] 3.1.3 Create developer guide for template rendering

### 3.2 Code cleanup
- [x] 3.2.1 Remove dead code (duplicate return statement)
- [x] 3.2.2 Consolidate imports
- [x] 3.2.3 Final lint pass - all checks passing
