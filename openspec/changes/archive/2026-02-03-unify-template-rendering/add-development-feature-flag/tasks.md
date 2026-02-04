# Tasks: Add Development Feature Flag

## Implementation Tasks

- [x] Add `guide-development` constant to feature flag constants
- [x] Add boolean validator for `guide-development` flag
- [x] Update `discover_commands()` to check flag before mtime validation
- [x] Add tests for cache behavior with flag enabled/disabled

## Testing Tasks

- [x] Test cache invalidation when flag is enabled
- [x] Test cache persistence when flag is disabled
- [x] Test flag validation rejects non-boolean values

## Documentation Tasks

- [~] Document `guide-development` flag in feature flags documentation (skipped - internal dev use only)
- [~] Add usage examples for development vs production (skipped - internal dev use only)
