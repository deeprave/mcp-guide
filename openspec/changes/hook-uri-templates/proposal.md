# Change: Hook URI Templates

## Why

Currently, the 'guide' agent runs a script on userPromptSubmit that displays static text, but this text cannot be rendered as a template. This creates limitations:

- Cannot render content based on feature flags
- Cannot use template variables like `{{_workflow.mode}}`
- Cannot use prompt characters like `{{@}}` in the text
- No dynamic content based on context or state

This forces all hook content to be static, preventing context-aware guidance and dynamic instructions.

## What Changes

Replace static script output with URI-based template instructions that agents can follow:

### Current Approach (Static)
```bash
# Script outputs static text
echo "🚨 You are in guided mode."
echo "DISCUSSION and PLANNING phases are required before implementation."
```

### New Approach (Template URI)
```bash
# Script outputs URI instruction
cat << EOF
---
Type: agent-instruction
Description: Mode-specific instructions
Instruction: Read this uri \`guide://_hooks/{{_workflow.mode}}\`
---
🚨 You are in guided mode.
Please read guide://_hooks/{{_workflow.mode}} for instructions
EOF
```

### Template Content Files
Create template-enabled content files at `_hooks/guided`, `_hooks/normal`, etc. that can:
- Use feature flags for conditional content
- Include template variables like `{{@}}` and `{{_workflow.mode}}`
- Render dynamic instructions based on context

### Agent Workflow
1. Agent receives URI instruction from script
2. Agent recognizes `guide://_hooks/{{_workflow.mode}}` pattern
3. Agent resolves template variables (e.g., `{{_workflow.mode}}` → "guided")
4. Agent calls `get_content(category_or_collection="_hooks/guided")`
5. Agent receives fully templated, feature-flag-aware content

## Impact

- **Requires:** add-guide-uri-scheme (for URI resolution)
- **Enables:** Dynamic hook content with full template support
- **Benefits:** Context-aware guidance, feature flag integration, template variables
- **Breaking:** None - existing static scripts continue to work
- **New capability:** Template-enabled hook instructions

## Dependencies

- **add-guide-uri-scheme**: Required for `guide://` URI resolution
- **template-support**: Required for template variable rendering in content
- **add-feature-flags**: Required for feature flag support in templates

## Success Criteria

- Hook scripts can output URI instructions with template variables
- Agents automatically follow and resolve guide:// URIs
- Template content supports feature flags and context variables
- Dynamic content renders correctly based on workflow mode
- Backward compatibility with existing static hook scripts
