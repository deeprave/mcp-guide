# Profiles

Profiles give you quick project setup with pre-configured categories and collections.

## What are Profiles?

Think of profiles as additive project guidance. Instead of manually selecting every
document, apply profiles for the languages, frameworks, platforms, build systems,
and test stacks that genuinely apply to the project.

## Discovering Profiles

Ask your AI agent what's available:

```
list all project profiles
What profiles are available?
```

The agent will show you available profiles and what they add to your project.

## Using Profiles

Just ask your AI agent to apply them:

```
Apply the python profile
Add the jira profile
```

## How Profiles Work

Profiles are **additive** - they add categories and collections without removing existing ones. You can apply multiple profiles to build up your project configuration:

```
Apply the python profile
Apply the jira profile
```

This gives you Python + Jira setup combined. Profiles can also describe different
parts of one technology stack:

```
Apply the swift profile
Apply the swiftui profile
Apply the ios profile
Apply the xctest profile
```

This composes base Swift language guidance, SwiftUI guidance, iOS build and test
guidance, and XCTest guidance. Applying the same profile multiple times has no effect.

Apply the `testing` profile to add the language-neutral testing guidance for any project.

## Profile guidance layout

- `lang/` holds base language, framework, and additive aspect guidance.
- `lang/build/` holds language and platform build guidance.
- `checks/` holds testing and verification guidance only.

The bundled catalogue includes established language profiles such as C, Swift,
Objective-C, Ruby, Dart, Scala, Elixir, Clojure, Lua, R, F#, Haskell, and Zig;
additive profiles including Node.js, Angular, Svelte, Nuxt, NestJS, Rails, Laravel,
Symfony, ASP.NET Core, Flutter, React Native, SwiftUI, UIKit, AppKit, Swift
Concurrency, Swift Package Manager, testing, XCTest, and Swift Testing; and platform profiles
for macOS, iOS, iPadOS, watchOS, tvOS, visionOS, Android, Windows, Linux, and browser
automation. Use `list_profiles` to see the authoritative installed set.

## Methodology and Policies

Methodology preferences (TDD, BDD, SOLID, YAGNI, DDD) are no longer configured through profiles. Instead, they are selected through the `policies` category. See [Policy Selection](policies.md) for details.
