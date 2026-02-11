# Implementation Tasks: Add User Documentation

## 1. General Usage Documentation

- [x] 1.1 Create overview of content delivery system
- [x] 1.2 Document categories configuration and usage
- [x] 1.3 Document collections configuration and usage
- [x] 1.4 Document feature flags system overview
- [x] 1.5 Add examples for common use cases

## 2. Pattern Syntax Documentation

- [x] 2.1 Create comprehensive pattern syntax guide (docs/patterns.md)
- [x] 2.2 Document glob pattern basics (*, **, ?, [])
- [x] 2.3 Document recursive directory matching
- [x] 2.4 Document file extension patterns (*.md, *.{py,js})
- [x] 2.5 Document directory-specific patterns (src/**/*.py)
- [x] 2.6 Add common use cases with examples
- [x] 2.7 Document integration with categories and collections

## 3. Output Format Documentation

- [x] 3.1 Create output formats guide (docs/output-formats.md)
- [x] 3.2 Document MIME-multipart format
- [x] 3.3 Document when to use vs plain format
- [x] 3.4 Document how to enable in tools
- [x] 3.5 Document output structure and boundaries
- [x] 3.6 Add use cases and integration scenarios
- [x] 3.7 Add practical examples

## 4. Document Management Documentation

- [x] 4.1 Create frontmatter reference guide
  - [x] 4.1.1 Document standard frontmatter keys
  - [x] 4.1.2 Document requires-* directives
  - [x] 4.1.3 Document includes directive
  - [x] 4.1.4 Add frontmatter examples
- [x] 4.2 Document commands system
  - [x] 4.2.1 Explain command discovery
  - [x] 4.2.2 Document command frontmatter keys
  - [x] 4.2.3 Add command examples
- [x] 4.3 Document client information exchange
  - [x] 4.3.1 Explain send_* tools purpose
  - [x] 4.3.2 Document send_file_content
  - [x] 4.3.3 Document send_directory_listing
  - [x] 4.3.4 Document send_working_directory
  - [x] 4.3.5 Document send_command_location

## 5. Templates Documentation

- [x] 5.1 Create template syntax guide (docs/templates.md)
- [x] 5.2 Document Chevron/Mustache syntax basics
- [x] 5.3 Document MCP Guide specific features
- [x] 5.4 Document file detection (.mustache, .hbs extensions)
- [x] 5.5 Document conditionals ({{#variable}}, {{^variable}})
- [x] 5.6 Document loops and iteration
- [x] 5.7 Add links to authoritative resources
- [x] 5.8 Document special functions
  - [x] 5.8.1 Document template functions
  - [x] 5.8.2 Document partials system
- [x] 5.9 Add practical template examples

## 6. Template Context Reference

- [x] 6.1 Create template context reference (docs/template-context.md)
- [x] 6.2 Document system context (timestamp, formatting)
- [x] 6.3 Document agent context (name, version, prefix)
- [x] 6.4 Document project context (name, flags, config)
- [x] 6.5 Document category context (metadata, files)
- [x] 6.6 Document file context (path, metadata)
- [x] 6.7 Document template functions (format_date, truncate, highlight_code)
- [x] 6.8 Document context hierarchy and precedence
- [x] 6.9 Document all template variables and lambdas

## 7. Feature Flags Documentation

- [x] 7.1 Create workflow flag documentation
  - [x] 7.1.1 Document workflow flag format
  - [x] 7.1.2 Document workflow-consent flag format
  - [x] 7.1.3 Document phase names and requirements
  - [x] 7.1.4 Document consent types (entry/exit)
  - [x] 7.1.5 Add workflow configuration examples
- [x] 7.2 Create openspec flag documentation
  - [x] 7.2.1 Document openspec flag purpose
  - [x] 7.2.2 Document openspec configuration
  - [x] 7.2.3 Add openspec examples
- [x] 7.3 Create client context flags documentation
  - [x] 7.3.1 Document allow-client-info flag
  - [x] 7.3.2 Document client information usage
  - [x] 7.3.3 Add client context examples

## 8. Commands and Guide Prompt Documentation

- [x] 8.1 Document @guide prompt basics
  - [x] 8.1.1 Explain command invocation format
  - [x] 8.1.2 Add one simple example with arguments
  - [x] 8.1.3 Document :help command for discovery

## 9. Organization & Review

- [x] 9.1 Organize documentation in appropriate directory structure
- [x] 9.2 Create table of contents / index
- [x] 9.3 Add cross-references between documents
- [x] 9.4 Update README with links to new documentation
- [x] 9.5 Update feature overview in README
- [x] 9.6 Review for completeness and clarity
- [x] 9.7 Add navigation aids
- [x] 9.8 Ensure consistent terminology
