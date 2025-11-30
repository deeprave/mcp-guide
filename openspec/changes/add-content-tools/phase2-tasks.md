# Phase 2: Template Support - Task Breakdowns

## Task 4.1: Add Mustache Library Dependency

**Description**: Add mustache template library as project dependency for template rendering.

**Requirements**:
- Add mustache library to pyproject.toml dependencies
- Lock dependency version
- Verify library installation
- Document library choice

**Assumptions**:
- Chevron is maintained and stable
- Library supports project Python version
- No conflicts with existing dependencies

**Acceptance Criteria**:
- [ ] mustache library added to pyproject.toml
- [ ] Dependency version appropriately constrained
- [ ] Dependency installation succeeds
- [ ] Library imports successfully in code
- [ ] No dependency conflicts
- [ ] Library choice documented in ADR or comments

---

## Task 4.2: Implement .mustache File Detection

**Description**: Implement file extension detection to identify mustache template files.

**Requirements**:
- Check file extension is `.mustache`
- Case-insensitive comparison
- Return boolean result
- Integrate with file discovery

**Assumptions**:
- Template files use `.mustache` extension
- Extension is sufficient for detection
- No other detection methods needed

**Acceptance Criteria**:
- [ ] Detects `.mustache` extension
- [ ] Case-insensitive (`.MUSTACHE` also detected)
- [ ] Returns True for template files
- [ ] Returns False for non-template files
- [ ] Integrates with content retrieval flow
- [ ] Unit tests verify detection logic

---

## Task 4.3: Implement Template Rendering

**Description**: Implement mustache template rendering using mustache library.

**Requirements**:
- Parse template content
- Render with context data
- Return rendered string
- Handle template syntax errors

**Assumptions**:
- Chevron handles mustache syntax
- Context is dictionary
- Templates are UTF-8 text

**Acceptance Criteria**:
- [ ] Renders simple variables: `{{var}}`
- [ ] Renders sections: `{{#section}}...{{/section}}`
- [ ] Renders inverted sections: `{{^section}}...{{/section}}`
- [ ] Renders partials: `{{>partial}}`
- [ ] Handles missing variables (empty string)
- [ ] Returns clear error for syntax errors
- [ ] Unit tests cover all mustache features

---

## Task 4.4: Add Pass-Through for Non-Template Files

**Description**: Implement logic to pass through non-template files unchanged.

**Requirements**:
- Check if file is template
- If not template, return content as-is
- If template, render and return
- Preserve content exactly for non-templates

**Assumptions**:
- Non-template files are majority
- Pass-through should be fast
- No processing needed for non-templates

**Acceptance Criteria**:
- [ ] Non-template files returned unchanged
- [ ] Template files are rendered
- [ ] Content preservation verified
- [ ] Non-templates processed efficiently
- [ ] Unit tests verify pass-through
- [ ] Unit tests verify rendering

---

## Task 4.5: Handle Template Syntax Errors

**Description**: Implement error handling for template syntax errors with clear messages.

**Requirements**:
- Catch library parsing errors
- Catch library rendering errors
- Return structured error
- Include error details (line, column if available)

**Assumptions**:
- Chevron raises exceptions for errors
- Error messages can be extracted
- Users need to fix template syntax

**Acceptance Criteria**:
- [ ] Catches parsing errors
- [ ] Catches rendering errors
- [ ] Returns `template_error` error type
- [ ] Error message includes file path
- [ ] Error message includes syntax details
- [ ] Agent instruction: "Present error to user for template fix"
- [ ] Unit tests verify error handling

---

## Task 4.6: Add Unit Tests for Template Detection

**Description**: Create unit tests for template file detection logic.

**Requirements**:
- Test various file extensions
- Test case sensitivity
- Test edge cases
- Meet project test coverage standards

**Assumptions**:
- Test fixtures provide sample filenames
- Tests are fast and isolated

**Acceptance Criteria**:
- [ ] Test `.mustache` detection
- [ ] Test `.MUSTACHE` detection (case-insensitive)
- [ ] Test `.md` not detected
- [ ] Test `.txt` not detected
- [ ] Test empty extension
- [ ] Test no extension
- [ ] All tests pass
- [ ] Unit tests meet project standards

---

## Task 4.7: Add Unit Tests for Rendering

**Description**: Create comprehensive unit tests for template rendering.

**Requirements**:
- Test all mustache syntax features
- Test with various contexts
- Test error cases
- Meet project test coverage standards

**Assumptions**:
- Test fixtures provide sample templates
- Tests verify rendered output

**Acceptance Criteria**:
- [ ] Test variable substitution
- [ ] Test sections
- [ ] Test inverted sections
- [ ] Test partials
- [ ] Test missing variables
- [ ] Test nested contexts
- [ ] Test HTML escaping
- [ ] All tests pass
- [ ] Unit tests meet project standards

---

## Task 4.8: Test Error Handling

**Description**: Create tests for template error handling scenarios.

**Requirements**:
- Test syntax errors
- Test rendering errors
- Verify error messages
- Verify error types

**Assumptions**:
- Errors can be triggered in tests
- Error messages are consistent

**Acceptance Criteria**:
- [ ] Test unclosed tag error
- [ ] Test invalid syntax error
- [ ] Test missing partial error
- [ ] Verify `template_error` type
- [ ] Verify error messages include details
- [ ] Verify agent instructions
- [ ] All tests pass

---

## Task 5.1: Define Context Sources (project, env, built-in)

**Description**: Define and document context sources for template rendering with priority order.

**Requirements**:
- Define project config as source
- Define environment variables as source
- Define built-in variables as source
- Document priority order
- Document available variables

**Assumptions**:
- Multiple sources may provide same variable
- Priority determines which value wins
- Sources are read-only

**Acceptance Criteria**:
- [ ] Priority order documented: project > env > built-in
- [ ] Project config source defined
- [ ] Environment variable source defined
- [ ] Built-in variable source defined
- [ ] Available variables documented
- [ ] Source interface defined
- [ ] Unit tests verify source definitions

---

## Task 5.2: Implement Context Priority and Merging

**Description**: Implement context merging logic that respects source priority.

**Requirements**:
- Merge contexts from all sources
- Apply priority order
- Handle missing variables
- Return merged dictionary

**Assumptions**:
- Higher priority sources override lower
- Missing variables are omitted
- Merging is done once per render

**Acceptance Criteria**:
- [ ] Project config overrides env and built-in
- [ ] Env overrides built-in
- [ ] Built-in provides defaults
- [ ] Missing variables handled gracefully
- [ ] Merged context is dictionary
- [ ] Unit tests verify priority
- [ ] Unit tests verify merging

---

## Task 5.3: Add Built-in Variables (project.name, timestamp, etc.)

**Description**: Implement built-in context variables for common template needs.

**Requirements**:
- `project.name`: Current project name
- `project.categories`: List of category names
- `project.collections`: List of collection names
- `timestamp`: Current timestamp (ISO 8601)
- `date`: Current date (YYYY-MM-DD)

**Assumptions**:
- Built-in variables are read-only
- Values are computed at render time
- Project info comes from session

**Acceptance Criteria**:
- [ ] `project.name` returns project name
- [ ] `project.categories` returns category list
- [ ] `project.collections` returns collection list
- [ ] `timestamp` returns ISO 8601 timestamp
- [ ] `date` returns YYYY-MM-DD date
- [ ] Variables accessible in templates
- [ ] Unit tests verify all variables

---

## Task 5.4: Implement Context Resolver

**Description**: Implement context resolver that gathers and merges context from all sources.

**Requirements**:
- Gather context from all sources
- Merge with priority
- Cache per request (optional)
- Return final context dictionary

**Assumptions**:
- Resolver called once per template render
- Sources are available
- Merging is fast

**Acceptance Criteria**:
- [ ] Gathers from all sources
- [ ] Merges with correct priority
- [ ] Returns dictionary
- [ ] Handles source errors gracefully
- [ ] Performance is acceptable
- [ ] Unit tests verify resolution
- [ ] Integration tests verify end-to-end

---

## Task 5.5: Add Unit Tests for Context Resolution

**Description**: Create unit tests for context resolution logic.

**Requirements**:
- Test each source
- Test priority merging
- Test missing variables
- Meet project test coverage standards

**Assumptions**:
- Test fixtures provide mock sources
- Tests verify merged output

**Acceptance Criteria**:
- [ ] Test project config source
- [ ] Test environment variable source
- [ ] Test built-in variable source
- [ ] Test priority override
- [ ] Test missing variables
- [ ] Test empty sources
- [ ] All tests pass
- [ ] Unit tests meet project standards

---

## Task 5.6: Test Context Priority Rules

**Description**: Create tests that verify context priority rules work correctly.

**Requirements**:
- Test priority order
- Test override behavior
- Test edge cases
- Document expected behavior

**Assumptions**:
- Priority rules are deterministic
- Tests can set up multiple sources

**Acceptance Criteria**:
- [ ] Test project overrides env
- [ ] Test project overrides built-in
- [ ] Test env overrides built-in
- [ ] Test same variable in all sources
- [ ] Test variable in only one source
- [ ] Test variable in no sources
- [ ] All tests pass

---

## Task 6.1: Implement Template Cache Structure

**Description**: Implement cache data structure for storing parsed templates.

**Requirements**:
- Store parsed template AST
- Key by file path
- Include metadata (mtime, size)
- Support get/set/delete operations

**Assumptions**:
- Dictionary is sufficient structure
- File path is unique key
- Memory usage is acceptable

**Acceptance Criteria**:
- [ ] Cache stores parsed templates
- [ ] Cache keyed by file path
- [ ] Cache includes file metadata
- [ ] Get operation returns cached template
- [ ] Set operation stores template
- [ ] Delete operation removes template
- [ ] Unit tests verify operations

---

## Task 6.2: Add Cache Hit/Miss Logic

**Description**: Implement cache lookup logic with hit/miss detection.

**Requirements**:
- Check if template in cache
- Validate cache entry is fresh
- Return cached template on hit
- Parse and cache on miss

**Assumptions**:
- Cache hits are common
- Cache validation is fast
- Parsing is expensive

**Acceptance Criteria**:
- [ ] Cache hit returns cached template
- [ ] Cache miss parses template
- [ ] Cache miss stores in cache
- [ ] Freshness check uses file mtime
- [ ] Stale entries treated as miss
- [ ] Unit tests verify hit/miss logic
- [ ] Performance improvement measurable

---

## Task 6.3: Implement Cache Invalidation on File Changes

**Description**: Implement cache invalidation when template files are modified.

**Requirements**:
- Detect file modification
- Compare mtime with cached mtime
- Invalidate stale entries
- Re-parse on next access

**Assumptions**:
- File mtime is reliable
- Modification detection is fast
- Invalidation is synchronous

**Acceptance Criteria**:
- [ ] Detects file modification via mtime
- [ ] Invalidates stale cache entries
- [ ] Re-parses modified templates
- [ ] Handles deleted files
- [ ] Handles new files
- [ ] Unit tests verify invalidation
- [ ] Integration tests verify behavior

---

## Task 6.4: Add Cache Size Limits and LRU Eviction

**Description**: Implement cache size limits with LRU (Least Recently Used) eviction policy.

**Requirements**:
- Set maximum cache size (entries or bytes)
- Track access time per entry
- Evict LRU entries when limit reached
- Configurable limit

**Assumptions**:
- LRU is good eviction policy
- Cache size limit prevents memory issues
- OrderedDict or similar provides LRU

**Acceptance Criteria**:
- [ ] Cache has configurable size limit
- [ ] Tracks access time per entry
- [ ] Evicts LRU entry when limit reached
- [ ] Eviction maintains cache consistency
- [ ] Default limit is reasonable (e.g., 100 entries)
- [ ] Unit tests verify eviction
- [ ] Unit tests verify LRU order

---

## Task 6.5: Add Unit Tests for Caching

**Description**: Create unit tests for template caching functionality.

**Requirements**:
- Test cache operations
- Test hit/miss scenarios
- Test invalidation
- Meet project test coverage standards

**Assumptions**:
- Test fixtures provide mock templates
- Tests can manipulate file mtimes

**Acceptance Criteria**:
- [ ] Test cache hit
- [ ] Test cache miss
- [ ] Test cache set
- [ ] Test cache delete
- [ ] Test freshness check
- [ ] Test stale entry
- [ ] All tests pass
- [ ] Unit tests meet project standards

---

## Task 6.6: Test Cache Invalidation

**Description**: Create tests for cache invalidation scenarios.

**Requirements**:
- Test file modification detection
- Test invalidation logic
- Test re-parsing
- Verify cache consistency

**Assumptions**:
- Tests can modify file mtimes
- Tests can verify cache state

**Acceptance Criteria**:
- [ ] Test invalidation on file change
- [ ] Test invalidation on file delete
- [ ] Test re-parsing after invalidation
- [ ] Test cache consistency maintained
- [ ] Test multiple invalidations
- [ ] All tests pass

---

## Task 6.7: Performance Testing

**Description**: Document caching behavior and verify cache functionality.

**Requirements**:
- Measure render time with cache
- Measure render time without cache
- Verify cache provides speedup
- Document caching behavior

**Assumptions**:
- Performance tests are repeatable
- Speedup is measurable

**Acceptance Criteria**:
- [ ] Benchmark render time with cache
- [ ] Benchmark render time without cache
- [ ] Cache provides ≥2x speedup
- [ ] Cache hit is ≥10x faster than parse
- [ ] Performance documented
- [ ] Tests run in CI
- [ ] No performance regressions
