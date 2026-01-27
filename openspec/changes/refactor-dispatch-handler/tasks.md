# Implementation Tasks

## Core Refactoring
- [ ] Update `dispatch_event` to return structured dict with all handler results
- [ ] Add `processed_count` to return dict (replace 'acknowledged'/'processed' status)
- [ ] Collect results from all handlers, not just first one
- [ ] Define standard result format: `{processed_count, handlers: [{template, template_type, context}]}`

## Dispatcher Function
- [ ] Create dispatcher function above `dispatch_event`
- [ ] Handle template rendering based on template_type (openspec, workflow, common)
- [ ] Pass additional context to template renderer
- [ ] Return Result without echoing received data

## Handler Updates
- [ ] Update event handlers to return dict with optional template info
- [ ] Remove Result returns from handlers (use dict format instead)
- [ ] Update OpenSpecTask to return template dict instead of Result

## Tool Updates
- [ ] Update filesystem tools to call dispatcher instead of dispatch_event
- [ ] Remove data echoing from tool responses
- [ ] Return clean Result.ok() without unnecessary data

## Testing
- [ ] Test multiple handlers returning results
- [ ] Test template rendering with different types
- [ ] Verify processed_count accuracy
- [ ] Test handlers without template info
