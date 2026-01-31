# Tasks: Add Development Feature Flag

## Implementation Tasks

- [x] Add `guide-development` constant to feature flag constants
- [x] Add boolean validator for `guide-development` flag
- [x] Update `discover_commands()` to check flag before mtime validation
- [ ] Add tests for cache behavior with flag enabled/disabled
- [ ] Update documentation for `guide-development` flag

## Testing Tasks

- [ ] Test cache invalidation when flag is enabled
- [ ] Test cache persistence when flag is disabled
- [ ] Test flag validation rejects non-boolean values

## Documentation Tasks

- [ ] Document `guide-development` flag in feature flags documentation
- [ ] Add usage examples for development vs production
