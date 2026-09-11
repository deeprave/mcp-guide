# language-profiles Specification

## Purpose

Provide bundled, composable language, framework, extension, platform, and build
guidance profiles for common software ecosystems not currently covered by Guide.

## Requirements

### Requirement: Base-language profiles
The system SHALL provide bundled, selectable base-language profiles for C, Swift,
Objective-C, Ruby, Dart, Scala, Elixir, Clojure, Lua, R, F#, Haskell, and Zig.
Each profile SHALL add focused guidance from the `lang` category without removing
existing category selections.

#### Scenario: Apply a base-language profile
- **WHEN** a user applies the `swift` profile
- **THEN** the project language category SHALL select Swift guidance
- **AND** existing language selections SHALL remain

### Requirement: Additive framework and aspect profiles
The system SHALL provide bundled, selectable additive profiles for Node.js,
Angular, Svelte, Nuxt, NestJS, Rails, Laravel, Symfony, ASP.NET Core, Flutter,
React Native, SwiftUI, UIKit, AppKit, Swift Concurrency, and Swift Package Manager.
Each profile SHALL add only its applicable focused language guidance.

#### Scenario: Compose a language and extension profile
- **WHEN** a user applies `swift` and `swiftui`
- **THEN** the project SHALL receive both base Swift and additive SwiftUI guidance
- **AND** applying either profile again SHALL not duplicate selections

### Requirement: Platform profiles
The system SHALL provide bundled, selectable platform profiles for macOS, iOS,
iPadOS, watchOS, tvOS, visionOS, Android, Windows, Linux, and browser/web automation.
A platform profile MAY select curated language-specific platform testing guidance
where it is normally relevant. Apple platform profiles SHALL select Swift guidance
by default and SHALL NOT select Objective-C guidance by default.

#### Scenario: Apply an Apple platform profile
- **WHEN** a user applies the `ipados` profile
- **THEN** the project language category SHALL select iPadOS platform guidance
- **AND** existing categories and collections SHALL remain

### Requirement: Build guidance hierarchy
The system SHALL store build guidance in `lang/build/` document paths within the
existing `lang` category. Language and platform profiles SHALL select applicable
build guidance where it can be determined without assuming unrelated profiles.

#### Scenario: Build guidance is language guidance
- **WHEN** a Swift platform profile selects build guidance
- **THEN** the selected document SHALL be under `lang/build/`
- **AND** it SHALL NOT be selected through the `checks` category
