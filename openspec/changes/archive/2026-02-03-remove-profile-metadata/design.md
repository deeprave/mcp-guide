# Design: Remove Profile Metadata

## Approach

Pure deletion - remove the `metadata` field and all code that reads or writes to it.

## Changes

1. **Project Model** - Remove `metadata: dict[str, Any]` field
2. **Profile Application** - Remove metadata tracking in `apply_to_project()`
3. **Formatting** - Remove metadata display in `format_project_data()`
4. **Tests** - Remove metadata assertions

## No Migration Needed

Existing config files with metadata are harmless - Pydantic ignores extra fields due to `ConfigDict(extra="ignore")`.
