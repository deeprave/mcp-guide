## REMOVED Requirements

### Requirement: get_flag Tool
**Reason**: Removed in `consolidate-tools`. Functionality merged into `list_project_flags` and `list_feature_flags` via optional `feature_name` parameter.
**Migration**: Use `list_project_flags(feature_name="my-flag")` or `list_feature_flags(feature_name="my-flag")` for single-flag retrieval.
