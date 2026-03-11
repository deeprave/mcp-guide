# Implementation Tasks

## Phase 1: Unify Frontmatter Processing

### 1.1 Create process_frontmatter() function
- [ ] 1.1.1 Add `process_frontmatter()` to `render/frontmatter.py`
  - Combines: parse + requirements check + instruction/description rendering
  - Returns: `Optional[ProcessedFrontmatter]` (None if filtered by requires-*)
  - Parameters: content (str), requirements_context (dict), render_context (Optional[TemplateContext])
- [ ] 1.1.2 Add `ProcessedFrontmatter` dataclass
  - Fields: frontmatter (Frontmatter), content (str), frontmatter_length (int), content_length (int)
- [ ] 1.1.3 Write tests for `process_frontmatter()`
  - Test parse + requirements check
  - Test instruction/description rendering
  - Test filtering (returns None when requires-* not met)

### 1.2 Replace usage in render/template.py
- [ ] 1.2.1 Replace lines 43-87 with `process_frontmatter()` call
- [ ] 1.2.2 Update tests to verify behavior unchanged

### 1.3 Replace usage in render/renderer.py
- [ ] 1.3.1 Replace lines 160-172 with `process_frontmatter()` call for partials
- [ ] 1.3.2 Update tests to verify behavior unchanged

### 1.4 Replace usage in render/partials.py
- [ ] 1.4.1 Replace lines 137-145 with `process_frontmatter()` call
- [ ] 1.4.2 Update tests to verify behavior unchanged

### 1.5 Replace usage in discovery/commands.py
- [ ] 1.5.1 Replace lines 118-135 with `process_frontmatter()` call
- [ ] 1.5.2 Update tests to verify behavior unchanged

### 1.6 Replace usage in content/utils.py
- [ ] 1.6.1 Replace lines 217-226 with `process_frontmatter()` call
- [ ] 1.6.2 Update tests to verify behavior unchanged

### 1.7 Validation
- [ ] 1.7.1 Run full test suite - all tests pass
- [ ] 1.7.2 Run ruff and mypy - no issues
- [ ] 1.7.3 Manual testing of commands and content retrieval

## Phase 2: Unify File Processing

### 2.1 Create process_file() function
- [ ] 2.1.1 Add `process_file()` to `render/frontmatter.py` or new module
  - Single entry point for template and non-template files
  - Uses `process_frontmatter()` internally
  - Handles template rendering via `render_template_content()`
  - Returns: `Optional[RenderedContent]`
  - Parameters: file_info (FileInfo), base_dir (Path), requirements_context (dict), template_context (Optional[TemplateContext])
- [ ] 2.1.2 Write tests for `process_file()`
  - Test template files
  - Test non-template files
  - Test requirements filtering

### 2.2 Simplify render/template.py
- [ ] 2.2.1 Refactor `render_template()` to use `process_file()`
- [ ] 2.2.2 Remove duplicate template vs non-template branching
- [ ] 2.2.3 Update tests

### 2.3 Simplify content/utils.py
- [ ] 2.3.1 Replace lines 195-226 with `process_file()` call
- [ ] 2.3.2 Remove duplicate template vs non-template branching
- [ ] 2.3.3 Update tests

### 2.4 Simplify discovery/commands.py
- [ ] 2.4.1 Remove inline frontmatter parsing (already done in Phase 1)
- [ ] 2.4.2 Consider using `process_file()` if applicable
- [ ] 2.4.3 Update tests

### 2.5 Validation
- [ ] 2.5.1 Run full test suite - all tests pass
- [ ] 2.5.2 Run ruff and mypy - no issues
- [ ] 2.5.3 Manual testing of all affected features
- [ ] 2.5.4 Performance check - no regressions

## Phase 3: Documentation and Cleanup

### 3.1 Update documentation
- [ ] 3.1.1 Update render/README.md with new API
- [ ] 3.1.2 Add docstrings to new functions
- [ ] 3.1.3 Update design docs if needed

### 3.2 Code cleanup
- [ ] 3.2.1 Remove any dead code
- [ ] 3.2.2 Consolidate imports
- [ ] 3.2.3 Final lint pass
