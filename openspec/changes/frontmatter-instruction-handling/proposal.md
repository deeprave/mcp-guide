# Change: Frontmatter Instruction Handling

## Why
The current content system includes raw frontmatter in output and ignores frontmatter instructions, causing users to see YAML metadata instead of clean content and agents to receive incorrect behavioral instructions.

## What Changes
- Fix MIME formatter to use `content_size` field for accurate HTTP Content-Length headers
- Strip frontmatter from content output in formatters
- Extract and use frontmatter `Instruction` field for Result instructions
- Implement type-based content handling (`user/information`, `agent/information`, `agent/instruction`)
- Add comprehensive test coverage for content_size integration

## Impact
- Affected specs: frontmatter-processing
- Affected code: content formatters, frontmatter utilities, content tools
- **BREAKING**: Content output format changes (frontmatter stripped)
