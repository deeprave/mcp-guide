# Implementation Tasks

## Core Refactoring
- [x] Create `EventResult` dataclass with:
  - [x] `result: bool` field (success=True, failure=False)
  - [x] `message: Optional[str]` field (simple string result)
  - [x] `rendered_content: Optional[RenderedContent]` field (rendered template)
- [x] Update `dispatch_event` to return `list[EventResult]`
- [x] Collect results from all handlers, not just first one

## Result Construction
- [x] Create helper function to build Result from EventResult list
- [x] For single EventResult:
  - [x] Use `rendered_content.instruction` if present (RenderedContent handles resolution)
  - [x] Use default instruction if no rendered_content
  - [x] Set `value` to `rendered_content.content` if rendered
  - [x] Set `message` from EventResult.message
- [x] For multiple EventResults:
  - [x] Success if all EventResult.result are True
  - [x] Deduplicate and concatenate all messages
  - [x] Concatenate all rendered_content.content in order
  - [x] Simple instruction deduplication (not using extract_and_deduplicate_instructions as it expects FileInfo)

## Handler Updates
- [x] Update event handlers to return `EventResult` objects
- [x] Handlers render templates themselves if needed (using appropriate render function)
- [x] Handlers return simple result+message if no rendering needed
- [x] Remove template type routing logic (handlers handle their own rendering)

## Tool Updates
- [x] Update filesystem tools to use new EventResult format
- [x] Remove data echoing from tool responses
- [x] Return clean Result constructed from EventResult list

## Testing
- [x] Test multiple handlers returning EventResult
- [x] Test EventResult with rendered_content
- [x] Test EventResult with simple message
- [x] Test Result construction with instruction override
- [x] Test handlers without rendered content

## Bug Fixes
- [x] Fix protocol: handlers return `EventResult | None` (not `EventResult | bool`)
- [x] Update all handlers to return `None` for unhandled events
- [x] Fix `aggregate_event_results` to handle success/failure split
- [x] Update all handler type annotations to `EventResult | None`

## Code Quality
- [x] Extract `combine_instructions()` into shared function
- [x] Refactor instruction combining logic in both modules
- [x] All tests pass (1444 tests)
- [x] All linting checks pass
- [x] All type checks pass
- [x] Code formatted
