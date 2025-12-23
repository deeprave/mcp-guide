# Change: Remove Project Tracking Dates

## Why
The project configuration includes `created_at` and `updated_at` fields that serve no practical purpose and add unnecessary complexity to the configuration.

## What Changes
- **BREAKING**: Remove `created_at` and `updated_at` fields from project configuration
- Update configuration loading to ignore legacy timestamp fields during migration
- Remove timestamp management logic from project operations

## Impact
- Affected specs: project-config
- Affected code: project configuration schema, loading, and saving logic
- Migration: Existing configurations will gracefully ignore these fields
