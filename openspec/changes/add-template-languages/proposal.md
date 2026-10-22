# Proposal

## Why

Guide profiles currently supply language and framework guidance, but offer no
focused help when a project uses a template language. Agents therefore receive
neither a concise language outline nor the language-specific safety and
maintainability practices needed to edit templates confidently.

## What Changes

- Add bundled, selectable profiles for commonly used template languages,
  initially Jinja2 and Mustache/Chevron.
- Add focused `lang/` documents for each profile that give an AI a concise
  language outline and practical authoring, escaping, partial/include, and
  testing guidance.
- Make the profile catalogue documentation describe the new template-language
  profiles and their additive use alongside programming-language and framework
  profiles.
- Keep the model open to additional template-language profiles without making
  their future selection, rendering, or runtime dependency part of this change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `language-profiles`: Add bundled, additive template-language profiles and
  their focused `lang/` guidance.
- `documentation`: Document the available template-language profiles and how
  they compose with other profiles.

## Impact

- Bundled profile definitions under `src/mcp_guide/templates/_profiles/`.
- Bundled language guidance under `src/mcp_guide/templates/_documents/lang/`.
- Profile catalogue documentation and profile discovery/onboarding coverage as
  required by the existing profile model.
- No template renderer, document format, external dependency, or configuration
  format change.
