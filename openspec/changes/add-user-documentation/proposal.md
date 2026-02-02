# Add User Documentation

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

The project currently lacks user-facing documentation. Users need brief, succinct guidance to get started and discover features without lengthy explanations.

Documentation should be:
- **Brief**: Minimal text, maximum clarity
- **Succinct**: Essential information only
- **Exploratory**: Point users to discovery mechanisms rather than exhaustive lists

Without this documentation, users must read source code to understand basic functionality.

## What Changes

Add comprehensive user documentation covering:

1. **General Usage**
   - Content delivery system overview
   - Categories and collections configuration
   - Feature flags introduction

2. **Document Management**
   - Frontmatter keys and values reference
   - Commands system and how they work
   - Client information exchange (send_* tools)

3. **Templates**
   - Template syntax overview
   - Conditionals and control flow
   - Special functions provided by the system

4. **Feature Flags** (separate documents for each)
   - Workflow flag and workflow-consent flag
   - OpenSpec support flag
   - Client context flags

5. **Commands and Guide Prompt**
   - Command invocation basics
   - Simple example
   - Using :help for discovery

## Impact

- **Affected specs**: help-template-system (adds user documentation requirement)
- **Affected code**: None (documentation only)
- **New files**: Multiple markdown documentation files in appropriate locations
