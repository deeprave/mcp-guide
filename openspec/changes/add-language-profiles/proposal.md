## Why

Bundled profiles cover a useful but incomplete set of languages and frameworks. Apple platform work, Swift, and dedicated test stacks have no first-class profiles, so agents cannot compose those projects the same way they compose Python, Kotlin, or Docker.

## What Changes

- Add Apple platform profiles for `ios`, `macos`, `watchos`, `tvos`, and `visionos`.
- Add language profiles for `swift` and `objective-c`.
- Add test profiles: a generic `testing` profile that selects existing check guidance, plus `xctest` and `swift-testing`.
- Offer the new profiles during onboarding whenever language, platform, or test-stack choices are collected.
- Keep profiles additive and idempotent; applying `swift` plus `ios` plus `xctest` composes without replacing existing project configuration.

Assumptions recorded for review:

- iPadOS uses the `ios` profile rather than a separate identifier.
- "Other languages" beyond Swift are deferred after this first wave; further languages reuse the same additive `lang` pattern.
- "Test profiles" means selectable test-stack profiles, not extra fixtures in the pytest suite.

## Capabilities

### New Capabilities

- `apple-platform-profiles`: Bundled profiles and guidance for Apple platforms.
- `language-profiles`: Bundled Swift and Objective-C language profiles and guidance.
- `test-profiles`: Bundled generic testing, XCTest, and Swift Testing profiles and guidance.

### Modified Capabilities

- `onboarding-state`: Offer the new language, platform, and test profiles where onboarding already offers technology choices.
- `documentation`: Keep user profile documentation aligned with the expanded set.

## Impact

- Bundled `_profiles` YAML, `lang/` and related templates, onboarding inspection hints, user profile documentation, and profile discovery or application tests.
- No change to the profile YAML schema, profile composition rules, or methodology/policy selection.
