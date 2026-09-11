## Why

Bundled profiles cover useful mainstream languages and a small number of frameworks, but omit major language ecosystems, mobile platforms, and their build and testing guidance. Agents therefore cannot compose language, framework, platform, and test-stack instructions for those projects as they can for existing Python, Kotlin, and Docker projects.

## What Changes

- Add base-language profiles for the highest-value missing languages: C, Swift, Objective-C, Ruby, Dart, Scala, Elixir, Clojure, Lua, R, F#, Haskell, and Zig.
- Add additive framework and language-aspect profiles for Node.js, Angular, Svelte, Nuxt, NestJS, Rails, Laravel, Symfony, ASP.NET Core, Flutter, React Native, SwiftUI, UIKit, AppKit, Swift Concurrency, Swift Package Manager, XCTest, and Swift Testing.
- Add platform profiles for macOS, iOS, iPadOS, watchOS, tvOS, visionOS, Android, Windows, Linux, and browser/web automation.
- Keep base language guidance in `lang/`, build guidance in `lang/build/`, and testing guidance in `checks/`.
- Have onboarding select every positively detected compatible profile, using the existing profile discovery and confirmation flow.
- Keep profile application additive and idempotent. A language, extension, platform, and test framework compose without replacing existing project configuration or needlessly repeating guidance.

## Capabilities

### New Capabilities

- `language-profiles`: Bundled base-language, framework, extension, and platform profiles with composable language and build guidance.
- `test-profiles`: Bundled testing-framework profiles and platform-specific test guidance.

### Modified Capabilities

- `onboarding-state`: Detect and stage every positively identified compatible profile for confirmation.
- `documentation`: Describe the expanded profile catalogue, composition model, and language/build/testing document layout.

## Impact

- Bundled `_profiles` YAML, `lang/`, `lang/build/`, and `checks/` templates.
- Onboarding inspection hints and profile application tests.
- User profile documentation.
- No change to profile YAML schema, profile composition rules, or methodology/policy selection.
