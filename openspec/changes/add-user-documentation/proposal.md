# Add User Documentation

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

The project currently lacks comprehensive user-facing documentation. Users need:
- Brief, succinct guidance to get started and discover features
- Understanding of pattern syntax for categories and collections
- Documentation of MIME-multipart output format
- Template syntax and context reference
- Feature flags and commands documentation

Without this documentation, users must read source code to understand basic functionality.

Documentation should be:
- **Brief**: Minimal text, maximum clarity
- **Succinct**: Essential information only
- **Exploratory**: Point users to discovery mechanisms rather than exhaustive lists

## What Changes

Add comprehensive user documentation covering:

1. **General Usage**
   - Content delivery system overview
   - Categories and collections configuration
   - Feature flags introduction

2. **Pattern Syntax**
   - Glob patterns, wildcards, recursive matching
   - File extension patterns
   - Integration with categories and collections

3. **Output Formats**
   - MIME-multipart format documentation
   - When to use vs plain format
   - Output structure and examples

4. **Document Management**
   - Frontmatter keys and values reference
   - Commands system and how they work
   - Client information exchange (send_* tools)

5. **Templates**
   - Template syntax overview (Chevron/Mustache)
   - Conditionals and control flow
   - Special functions provided by the system
   - Complete template context reference
   - Available variables and functions organized by group

6. **Feature Flags** (separate documents for each)
   - Workflow flag and workflow-consent flag
   - OpenSpec support flag
   - Client context flags

7. **Commands and Guide Prompt**
   - Command invocation basics
   - Simple example
   - Using :help for discovery

## Impact

- **Affected specs**: help-template-system (adds user documentation requirement)
- **Affected code**: None (documentation only)
- **New files**: Multiple markdown documentation files in appropriate locations
- **Replaces**: user-documentation-updates change (merged into this change)
