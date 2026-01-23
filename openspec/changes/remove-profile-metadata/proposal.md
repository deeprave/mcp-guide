# Remove Profile Metadata Tracking

## Problem

The `applied_profiles` metadata field violates YAGNI - it tracks which profiles were applied to a project but serves no functional purpose. Profiles are already applied (categories and collections exist), so tracking their names is unnecessary complexity.

## Why It's Unnecessary

1. **No functional use**: Nothing reads or uses `applied_profiles` for any decision-making
2. **Redundant**: The actual profile effects (categories/collections) are already in the project
3. **Idempotency handled differently**: Profile application checks if categories/collections already exist, not metadata
4. **Over-engineering**: Adds complexity without solving any actual problem

## Solution

Remove all `applied_profiles` metadata tracking:
- Remove metadata field from Project model
- Remove tracking logic from Profile.apply_to_project()
- Remove display logic from format_project_data()
- Remove from tests

Profiles remain fully functional - they add categories and collections. That's all they need to do.

## Impact

- **Breaking change**: None - metadata was never used functionally
- **Migration**: None needed - existing metadata is harmless and ignored
- **Tests**: Update tests to not expect metadata field
