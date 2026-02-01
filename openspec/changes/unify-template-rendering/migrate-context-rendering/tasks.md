# Tasks: Migrate Context Rendering

## Template Organization
- [x] Move templates from `_common/` to `_context/` directory
- [x] Add `CONTEXT_DIR` constant to `config_constants.py`

## Implementation
- [x] Update `context/rendering.py` to use `render_content()`
- [x] Change return type to `RenderedContent | None`
- [x] Remove `render_system_content` import and usage
- [x] Update `context/tasks.py` to extract `.content` from `RenderedContent`
- [x] Handle `None` return for filtered templates

## Testing
- [x] Verify existing context rendering tests pass
- [x] Test that client context setup still works
- [x] Test that client context detailed rendering works

## Cleanup
- [x] Remove unused imports from `context/rendering.py`
- [x] Verify no other code references `_common` directory
