## 1. Investigation
- [ ] 1.1 Add debug logging to `get_resolved_flag_value()` to capture flag resolution
- [ ] 1.2 Add logging to `_ConfigManager.get_feature_flags()` to track cache hits/misses
- [ ] 1.3 Add logging to `get_formatter_from_flag()` to verify formatter selection
- [ ] 1.4 Reproduce the issue with logging enabled to identify root cause

## 2. Fix Implementation
- [ ] 2.1 Fix caching issue in ConfigManager or flag resolution
- [ ] 2.2 Replace bare `except Exception` in `get_resolved_flag_value()` with specific exceptions
- [ ] 2.3 Add proper error logging for flag resolution failures
- [ ] 2.4 Ensure cache invalidation works across session instances

## 3. Testing
- [ ] 3.1 Write test: set flag, verify immediate effect on next content request
- [ ] 3.2 Write test: flag changes propagate across multiple session instances
- [ ] 3.3 Manual test: set content-format=mime, verify MIME headers in response
- [ ] 3.4 Manual test: change flag multiple times, verify each change takes effect

## 4. Verification
- [ ] 4.1 Run all existing tests
- [ ] 4.2 Verify no regression in flag resolution
- [ ] 4.3 Confirm logging doesn't impact performance
