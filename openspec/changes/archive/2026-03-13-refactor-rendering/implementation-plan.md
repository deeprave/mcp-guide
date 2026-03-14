# Implementation Plan: refactor-rendering

## Overview
Progressive refactor to unify frontmatter processing and file rendering across the codebase. Eliminates ~200-300 lines of duplication while maintaining backward compatibility.

## Prerequisites
- All existing tests passing
- Python 3.10+
- Existing modules: `render/frontmatter.py`, `render/template.py`, `render/renderer.py`, `render/partials.py`, `discovery/commands.py`, `content/utils.py`

## Phase 1: Unify Frontmatter Processing

**BRANCH**: Create `feature/refactor-rendering-phase1` from current branch

### Goal
Create single `process_frontmatter()` function that combines:
1. Parse frontmatter from content
2. Check `requires-*` directives against context
3. Render `instruction` and `description` fields as templates

### 1.1 RED: Write failing test for process_frontmatter()

**File**: `tests/test_render/test_process_frontmatter.py` (new)

**Tests to write**:
```python
async def test_process_frontmatter_basic():
    """Test basic frontmatter parsing without requirements."""
    content = """---
type: agent/instruction
instruction: Test instruction
---
Content here"""

    result = await process_frontmatter(content, {}, None)

    assert result is not None
    assert result.frontmatter["type"] == "agent/instruction"
    assert result.frontmatter["instruction"] == "Test instruction"
    assert result.content == "Content here"

async def test_process_frontmatter_requirements_met():
    """Test frontmatter with satisfied requirements."""
    content = """---
requires-feature: true
---
Content"""

    result = await process_frontmatter(content, {"feature": True}, None)

    assert result is not None

async def test_process_frontmatter_requirements_not_met():
    """Test frontmatter with unsatisfied requirements returns None."""
    content = """---
requires-feature: true
---
Content"""

    result = await process_frontmatter(content, {"feature": False}, None)

    assert result is None

async def test_process_frontmatter_render_instruction():
    """Test instruction field rendered as template."""
    content = """---
instruction: Hello {{name}}
---
Content"""
    context = TemplateContext({"name": "World"})

    result = await process_frontmatter(content, {}, context)

    assert result is not None
    assert result.frontmatter["instruction"] == "Hello World"

async def test_process_frontmatter_render_description():
    """Test description field rendered as template."""
    content = """---
description: Project {{project}}
---
Content"""
    context = TemplateContext({"project": "test"})

    result = await process_frontmatter(content, {}, context)

    assert result is not None
    assert result.frontmatter["description"] == "Project test"

async def test_process_frontmatter_render_error_graceful():
    """Test rendering error handled gracefully with warning."""
    content = """---
instruction: Hello {{missing}}
---
Content"""

    result = await process_frontmatter(content, {}, TemplateContext({}))

    # Should not raise, should log warning
    assert result is not None
```

**Run**: `pytest tests/test_render/test_process_frontmatter.py` → FAIL (function doesn't exist)

### 1.2 GREEN: Implement process_frontmatter()

**File**: `src/mcp_guide/render/frontmatter.py`

**Add dataclass**:
```python
@dataclass
class ProcessedFrontmatter:
    """Result of frontmatter processing."""
    frontmatter: Frontmatter
    content: str
    frontmatter_length: int
    content_length: int
```

**Add function**:
```python
async def process_frontmatter(
    content: str,
    requirements_context: Dict[str, Any],
    render_context: Optional[TemplateContext] = None,
) -> Optional[ProcessedFrontmatter]:
    """Process frontmatter: parse, check requirements, render fields.

    Args:
        content: Raw content with frontmatter
        requirements_context: Context for requires-* checking
        render_context: Optional context for rendering instruction/description

    Returns:
        ProcessedFrontmatter if requirements met, None if filtered
    """
    # Parse frontmatter
    parsed = parse_content_with_frontmatter(content)

    # Check requirements
    if not check_frontmatter_requirements(parsed.frontmatter, requirements_context):
        return None

    # Render instruction and description fields if render_context provided
    if render_context:
        context_dict = dict(render_context)
        for field in ("instruction", "description"):
            if field in parsed.frontmatter and isinstance(parsed.frontmatter[field], str):
                try:
                    import chevron
                    parsed.frontmatter[field] = chevron.render(
                        parsed.frontmatter[field], context_dict
                    )
                except chevron.ChevronError as e:
                    logger.warning(f"Failed to render {field} field: {e}")

    return ProcessedFrontmatter(
        frontmatter=parsed.frontmatter,
        content=parsed.content,
        frontmatter_length=parsed.frontmatter_length,
        content_length=parsed.content_length,
    )
```

**Export**: Add to `__all__` in `render/frontmatter.py`

**Run**: `pytest tests/test_render/test_process_frontmatter.py` → PASS

### 1.3 REFACTOR: Clean up implementation

- Extract field rendering to helper function if needed
- Ensure error handling is consistent
- Add type hints
- Add docstrings

**Run**: `pytest tests/test_render/test_process_frontmatter.py` → PASS

### 1.4 Replace usage in render/template.py

**RED**: Write test to verify behavior unchanged
```python
async def test_render_template_uses_process_frontmatter():
    """Verify render_template uses process_frontmatter internally."""
    # Test that existing behavior is preserved
```

**GREEN**: Replace lines 43-87 with `process_frontmatter()` call

**REFACTOR**: Simplify code, remove duplication

**Run**: `pytest tests/test_render_template.py` → PASS

**CHECKPOINT 1**: Stop for manual testing of template rendering
- User creates branch: `git checkout -b checkpoint/template-replacement`
- If tests pass, user commits: `git commit -m "refactor: use process_frontmatter in render/template.py"`
- This isolates template.py changes for diagnosis if issues found

### 1.5 Replace usage in render/renderer.py

**RED**: Write test for partial frontmatter rendering
**GREEN**: Replace lines 160-172 with `process_frontmatter()` call
**REFACTOR**: Clean up

**Run**: `pytest tests/test_render/test_renderer.py` → PASS

### 1.6 Replace usage in render/partials.py

**RED**: Write test for partial loading with requirements
**GREEN**: Replace lines 137-145 with `process_frontmatter()` call
**REFACTOR**: Clean up

**Run**: `pytest tests/test_render/test_partials.py` → PASS

### 1.7 Replace usage in discovery/commands.py

**RED**: Write test for command discovery with requirements
**GREEN**: Replace lines 118-135 with `process_frontmatter()` call
**REFACTOR**: Clean up

**Run**: `pytest tests/test_discovery/test_commands.py` → PASS

### 1.8 Replace usage in content/utils.py

**RED**: Write test for content loading with requirements
**GREEN**: Replace lines 217-226 with `process_frontmatter()` call
**REFACTOR**: Clean up

**Run**: `pytest tests/test_content/test_utils.py` → PASS

**CHECKPOINT 2**: Stop for manual testing of content retrieval
- If tests pass, user commits: `git commit -m "refactor: use process_frontmatter in content/utils.py"`
- This isolates content/utils.py changes for diagnosis

### 1.9 Phase 1 Validation

**STOP POINT 1: Manual Testing Required**

Automated checks:
- [ ] Run full test suite: `pytest`
- [ ] Run type checking: `mypy src`
- [ ] Run linting: `ruff check src tests`
- [ ] Run formatting: `ruff format src tests`

Manual testing (user to perform):
- [ ] Test command execution: `@guide :help`
- [ ] Test content retrieval: `@guide docs`
- [ ] Test template rendering with variables
- [ ] Check for deadlocks or async issues
- [ ] Verify no performance degradation

**DO NOT PROCEED TO PHASE 2 WITHOUT USER APPROVAL**

**If approved**: User commits final Phase 1 changes and merges checkpoint branch back to feature branch

## Phase 2: Unify File Processing

**BRANCH**: Create `feature/refactor-rendering-phase2` from Phase 1 branch

### Goal
Create single `process_file()` function that:
1. Uses `process_frontmatter()` internally
2. Handles both template and non-template files
3. Returns `RenderedContent` consistently

### 2.1 RED: Write failing test for process_file()

**File**: `tests/test_render/test_process_file.py` (new)

**Tests to write**:
```python
async def test_process_file_template():
    """Test processing template file."""
    # Create FileInfo for .mustache file
    # Call process_file()
    # Verify template rendered

async def test_process_file_non_template():
    """Test processing non-template file."""
    # Create FileInfo for .md file
    # Call process_file()
    # Verify content returned as-is

async def test_process_file_requirements_not_met():
    """Test file filtered by requirements."""
    # Create FileInfo with requires-* frontmatter
    # Call process_file() with unsatisfied requirements
    # Verify returns None
```

**Run**: `pytest tests/test_render/test_process_file.py` → FAIL

### 2.2 GREEN: Implement process_file()

**File**: `src/mcp_guide/render/frontmatter.py` or new module

**Add function**:
```python
async def process_file(
    file_info: FileInfo,
    base_dir: Path,
    requirements_context: Dict[str, Any],
    template_context: Optional[TemplateContext] = None,
) -> Optional[RenderedContent]:
    """Process file: parse frontmatter, render if template.

    Args:
        file_info: File to process
        base_dir: Base directory for template resolution
        requirements_context: Context for requires-* checking
        template_context: Optional context for template rendering

    Returns:
        RenderedContent if requirements met, None if filtered
    """
    # Read content
    content = await read_file_content(file_info.path)

    # Process frontmatter
    processed = await process_frontmatter(content, requirements_context, template_context)
    if processed is None:
        return None

    # Render if template file
    if is_template_file(file_info):
        # Use render_template_content()
        result = await render_template_content(
            processed.content,
            template_context or TemplateContext({}),
            str(file_info.path),
            metadata=dict(processed.frontmatter),
            base_dir=base_dir,
        )
        if not result.success:
            raise RuntimeError(f"Template rendering failed: {result.error}")
        rendered_content, partial_frontmatter = result.value
    else:
        rendered_content = processed.content
        partial_frontmatter = []

    return RenderedContent(
        frontmatter=processed.frontmatter,
        frontmatter_length=processed.frontmatter_length,
        content=rendered_content,
        content_length=len(rendered_content),
        template_path=file_info.path,
        template_name=file_info.path.name,
        partial_frontmatter=partial_frontmatter,
    )
```

**Run**: `pytest tests/test_render/test_process_file.py` → PASS

### 2.3 REFACTOR: Clean up implementation

- Ensure error handling is consistent
- Add type hints
- Add docstrings

**Run**: `pytest tests/test_render/test_process_file.py` → PASS

### 2.4 Simplify render/template.py

**RED**: Write test to verify behavior unchanged
**GREEN**: Refactor `render_template()` to use `process_file()`
**REFACTOR**: Remove duplicate branching logic

**Run**: `pytest tests/test_render_template.py` → PASS

### 2.5 Simplify content/utils.py

**RED**: Write test to verify behavior unchanged
**GREEN**: Replace lines 195-226 with `process_file()` call
**REFACTOR**: Remove duplicate branching logic

**Run**: `pytest tests/test_content/test_utils.py` → PASS

**CHECKPOINT 3**: Stop for manual testing of unified file processing
- User creates branch: `git checkout -b checkpoint/unified-file-processing`
- If tests pass, user commits: `git commit -m "refactor: use process_file in content/utils.py"`
- This isolates unified file processing changes for diagnosis

### 2.6 Phase 2 Validation

**STOP POINT 2: Manual Testing Required**

Automated checks:
- [ ] Run full test suite: `pytest`
- [ ] Run type checking: `mypy src`
- [ ] Run linting: `ruff check src tests`
- [ ] Run formatting: `ruff format src tests`

Manual testing (user to perform):
- [ ] Test all command types (help, create, etc.)
- [ ] Test content retrieval from multiple categories
- [ ] Test template files with partials
- [ ] Test non-template files
- [ ] Check for deadlocks or async issues
- [ ] Verify no performance degradation
- [ ] Test edge cases (missing files, invalid templates)

**DO NOT PROCEED TO PHASE 3 WITHOUT USER APPROVAL**

**If approved**: User commits final Phase 2 changes and merges checkpoint branch back to feature branch

## Phase 3: Documentation and Cleanup

### 3.1 Update documentation

- [ ] Update `src/mcp_guide/render/README.md` with new API
- [ ] Add comprehensive docstrings to new functions
- [ ] Update any design docs if needed

### 3.2 Code cleanup

- [ ] Remove any dead code
- [ ] Consolidate imports
- [ ] Final lint pass: `ruff check src tests`
- [ ] Final format pass: `ruff format src tests`

### 3.3 Final validation

- [ ] Run full test suite: `pytest --cov`
- [ ] Verify coverage: `pytest --cov-report=term-missing`
- [ ] Run mypy: `mypy src`
- [ ] Run pre-commit: `pre-commit run --all-files`

## Success Criteria

1. All tests pass (100% of existing tests + new tests)
2. No mypy errors
3. No ruff warnings
4. Code coverage maintained or improved
5. ~200-300 lines of duplication removed
6. All pipelines (commands, content, partials) work correctly
7. No performance regressions
8. Documentation updated

## Estimated Effort

- Phase 1: 3-4 hours (TDD cycles for process_frontmatter + 5 replacements)
- Phase 2: 2-3 hours (TDD cycles for process_file + 2 simplifications)
- Phase 3: 1 hour (documentation + cleanup)

**Total: 6-8 hours**

## Notes

- Follow TDD strictly: RED → GREEN → REFACTOR for each step
- Run tests after every change
- Keep commits small and focused
- Each phase should be independently testable
- Maintain backward compatibility throughout
- No changes to public APIs
