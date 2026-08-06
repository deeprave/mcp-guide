## Why

The default profile does not consistently expose its available review guidance, and profiles can declare collections without any usable category expression. Docker and shell-script projects also lack first-class language guidance.

## What Changes

- Add a Docker profile and Docker best-practices guidance.
- Add shell scripting as a language option, covering Bash, Zsh, and compatible shell scripts.
- Add the code-review collection and baseline check guidance to the default profile.
- Validate that every profile collection references at least one category or expression, and correct the default review category pattern to select `general`.
- Verify that every static bundled resource reference in a template targets a real, non-empty renderable resource in the configuration where that feature is enabled.

## Capabilities

### New Capabilities

- `docker-profile`: Provide Docker-specific guidance and profile configuration.
- `shell-language-profile`: Provide shell scripting guidance and language-profile selection.

### Modified Capabilities

- `models`: Validate profile collections and apply the expanded default profile safely.
- `onboarding-state`: Present Docker and shell scripting among selectable project technologies.
- `template-resource-integrity`: Keep static template resource references aligned with bundled documents, profiles, and commands.

## Impact

- Profile YAML, bundled template resource references, language and review templates, profile validation, onboarding, and tests.
