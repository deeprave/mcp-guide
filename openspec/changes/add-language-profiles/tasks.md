## 1. Profile catalogue and language guidance

- [x] 1.1 Add bundled base-language profiles and focused `lang/` guidance for C, Swift, Objective-C, Ruby, Dart, Scala, Elixir, Clojure, Lua, R, F#, Haskell, and Zig; verify every profile is discoverable and selects non-empty guidance.
- [x] 1.2 Add bundled additive profiles and `lang/` guidance for Node.js, Angular, Svelte, Nuxt, NestJS, Rails, Laravel, Symfony, ASP.NET Core, Flutter, React Native, SwiftUI, UIKit, AppKit, Swift Concurrency, and Swift Package Manager; verify each composes with its corresponding base language profile without duplicate patterns.

## 2. Platforms, build guidance, and testing guidance

- [x] 2.1 Add bundled platform profiles for macOS, iOS, iPadOS, watchOS, tvOS, visionOS, Android, Windows, Linux, and browser/web automation; verify each is discoverable and additive.
- [x] 2.2 Add focused `lang/build/` documents for the supported language/platform combinations and select them through language/platform profiles where positive selection is possible; verify build guidance is not selected through `checks`.
- [x] 2.3 Add platform-specific `checks/<language>/<platform>/` guidance and shared test-framework guidance where grouping avoids repetition; add `testing`, `xctest`, and `swift-testing` profiles and verify they compose with language/platform profiles.

## 3. Onboarding and documentation

- [x] 3.1 Extend onboarding inspection hints for positively identifiable language, framework, platform, build, and test markers; verify onboarding obtains identifiers from `list_profiles` and stages every positive compatible profile for confirmation.
- [x] 3.2 Update user profile documentation to explain the composition model, the `lang/`, `lang/build/`, and `checks/` responsibilities, and the expanded profile catalogue; verify every named example refers to an existing profile.

## 4. Verification

- [x] 4.1 Add focused profile discovery, application, composition, and onboarding tests for the new profiles, then run the relevant pytest selection in a foreground terminal and verify it passes.
- [x] 4.2 Run `openspec validate add-language-profiles --type change --strict` and verify no validation errors remain.
