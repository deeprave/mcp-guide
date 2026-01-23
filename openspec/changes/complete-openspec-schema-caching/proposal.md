# Complete OpenSpec Schema Caching Integration

## Overview

Complete the remaining OpenSpec integration tasks to support schema caching in feature flags, schema field in workflow state, and template context access to schemas.

## Problem

OpenSpec schemas are retrieved via `:openspec/schemas` command but not cached or accessible in templates. The workflow file lacks a schema field to track which OpenSpec schema applies to the current issue.

## Solution

- Cache schemas in feature flag object when received from OpenSpec CLI
- Add optional `schema` field to workflow state for tracking current OpenSpec schema
- Expose cached schemas in template context via `openspec.schemas`
- Update workflow schema to support schema field persistence

## Impact

- Templates can conditionally render based on available OpenSpec schemas
- Workflow state tracks which schema applies to current work
- Feature flag object provides single source of truth for OpenSpec metadata
- No breaking changes - schema field is optional

## Related

- OpenSpec CLI integration (already implemented)
- Feature flag system (already implemented)
- Workflow state management (already implemented)
