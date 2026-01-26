# Remove Profile Metadata Tracking

## Why

The `applied_profiles` metadata field violates YAGNI - it tracks which profiles were applied to a project but serves no functional purpose. Nothing reads or uses this metadata for any decision-making. The actual profile effects (categories and collections) are already in the project, making the tracking redundant. Profile idempotency is handled by checking if categories/collections already exist, not by checking metadata.

## What Changes

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
