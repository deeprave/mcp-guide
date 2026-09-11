## Context

Profiles are additive YAML files under the bundled `_profiles` directory. A profile contributes category patterns; applying several profiles merges those patterns idempotently. The default profile already provides `lang` and `checks` categories. Category names cannot contain `/`, but category patterns and document paths can, so `lang/build/` is a document hierarchy inside the existing `lang` category rather than a new category.

The project already provides base profiles for Python, JavaScript, TypeScript, Java, Kotlin, C#, C++, Go, Rust, PHP, SQL, shell, and selected frameworks. This change fills the highest-value gaps while establishing a repeatable catalogue structure for later additions.

## Goals / Non-Goals

**Goals:**

- Reuse profile discovery, application, and the existing YAML schema without loader or model changes.
- Model a project as independently composable base-language, extension/framework, platform, and test-stack selections.
- Keep guidance additive: documents contribute focused material and only repeat important fundamentals.
- Place language guidance in `lang/`, build guidance in `lang/build/`, and testing/verification guidance in `checks/`.
- Detect and stage every compatible profile that onboarding can positively identify, while retaining user confirmation.
- Add all named platform profiles now; expand individual guidance later where it requires deeper ecosystem coverage.

**Non-Goals:**

- A new profile schema, platform category, or `lang/build` category name.
- Creating a profile for every language/framework/platform combination.
- Changing testing-policy documents (`policies/testing/*`) or methodology selection.
- User-defined or out-of-tree profile directories.

## Decisions

1. **Composable profiles instead of use-case profiles**
   - `swift` contributes base language guidance. `swiftui`, `swift-concurrency`, and similar profiles contribute only additive aspect guidance. `ios`, `xctest`, and other compatible selections compose with it.
   - This avoids combinations such as `swift-ios-xctest`, which cannot scale and repeat the same material.

2. **Language owns build guidance; checks own testing**
   - Build documents use paths such as `lang/build/swift/ios.mustache` and are selected by language and platform profiles where possible.
   - Testing documents use paths such as `checks/swift/ios.mustache`; shared framework guidance may use a grouped path such as `checks/swift/xctest.mustache`.
   - `checks` remains exclusively for testing and verification; `lang/build` is not a category name because category identifiers cannot contain slashes.

3. **Base, extension, platform, and test profiles are independently selectable**
   - Base profiles cover C, Swift, Objective-C, Ruby, Dart, Scala, Elixir, Clojure, Lua, R, F#, Haskell, and Zig.
   - Additive profiles cover Node.js, Angular, Svelte, Nuxt, NestJS, Rails, Laravel, Symfony, ASP.NET Core, Flutter, React Native, SwiftUI, UIKit, AppKit, Swift Concurrency, Swift Package Manager, XCTest, and Swift Testing.
   - Platform profiles cover macOS, iOS, iPadOS, watchOS, tvOS, visionOS, Android, Windows, Linux, and browser/web automation.
   - Later changes may deepen a profile but should not invent combination profiles.

4. **Onboarding stages every positive detection**
   - Inspection markers identify compatible base, framework, platform, build, and test profiles. Onboarding obtains valid identifiers through `list_profiles`, stages all positively detected matches, and lets the user confirm them.
   - Where markers establish a close match rather than an exact target, the closest profile may be staged. For example, an Xcode project establishes an Apple/Xcode context but must not assert an Apple platform absent target evidence.

5. **Platform-specific build and test material remains focused**
   - macOS guidance may cover native UI automation. iOS, iPadOS, tvOS, watchOS, visionOS, and Android guidance covers simulator/device or hidden-window constraints as appropriate.
   - Documents should state durable workflow guidance, not volatile SDK/API inventories.

## Risks / Trade-offs

- [Catalogue breadth dilutes guidance] → Each profile has a small, focused document; follow-up changes deepen coverage instead of duplicating general advice.
- [Marker ambiguity selects an incorrect profile] → Stage only positive evidence and preserve confirmation; do not infer platform solely from a general Xcode marker.
- [Overlap across language, build, and testing documents] → Keep each document’s responsibility explicit and repeat only important fundamentals.

## Migration Plan

- Ship bundled YAML files and templates using the existing profile mechanism. No project configuration migration is required.
- Existing projects gain profiles only when a user or onboarding applies them.
- Rollback removes newly bundled profile files and templates; applied projects retain already merged category patterns.
