## Context

See [proposal.md](proposal.md) for motivation. Profiles are additive YAML files under the bundled `_profiles` directory. Language and framework profiles add patterns to the `lang` category; Docker already uses that same category for a non-language technology. Guidance lives in matching `lang/<pattern>.mustache` documents. Discovery lists every non-underscore `*.yaml` basename. Onboarding asks for language and framework profiles after calling `list_profiles`, and already mentions Docker and shell.

`fix-profile-traversal` is in progress and hardens profile identifier and containment rules. New profile names MUST remain simple basenames (`swift`, `objective-c`, `swift-testing`) so they stay valid under that loader.

## Goals / Non-Goals

**Goals:**

- Reuse the existing profile schema, discovery, and apply path with no loader or model changes.
- Give each new profile a matching bundled guidance document so applying it produces non-empty `lang` or `checks` content.
- Keep Apple language, platform, and test-stack selections independently composable.
- Extend onboarding inspection hints so Xcode and Swift package markers can propose the new profiles.

**Non-Goals:**

- A new `platform` category or profile YAML fields.
- A separate iPadOS profile.
- Additional languages beyond Swift and Objective-C in this wave.
- Changing testing-policy documents (`policies/testing/*`) or methodology selection.
- User-defined or out-of-tree profile directories.

## Decisions

1. **Reuse `lang` for Apple platforms**
   - Platform profiles add a `lang` pattern (`ios`, `macos`, and so on) and a `lang/<platform>.mustache` document, matching Docker.
   - Alternative considered: add a `platform` category to `_default`. Rejected because it changes the default profile surface for every project and is not needed for composition.

2. **Keep language, platform, and test-stack profiles separate**
   - `swift` does not imply `ios`; `ios` does not imply `xctest`.
   - Alternative considered: one `ios` profile that also selects Swift and XCTest. Rejected because macOS, server-side Swift, and mixed test stacks would then have to undo bundled defaults.

3. **Generic `testing` selects existing checks guidance**
   - The `testing` profile adds the `testing` pattern to the `checks` category, which already has `checks/testing.mustache`.
   - `xctest` and `swift-testing` add `lang` patterns with dedicated guidance, because they are framework-specific rather than another testing posture.
   - Alternative considered: fold XCTest into the generic testing profile. Rejected because XCTest is not the only Apple test stack.

4. **Hyphenated profile identifiers**
   - Use `objective-c` and `swift-testing` as YAML basenames. They match existing `c-sharp` and `c-plusplus` naming and remain simple basenames.
   - Alternative considered: `objc` and `swifttesting`. Rejected because the hyphenated forms are clearer in `list_profiles` output.

5. **Onboarding uses discovery rather than a hard-coded technology list**
   - Onboarding already calls `list_profiles`. Add inspection hints (Xcode project, `Package.swift`, `.xctestplan`) and mention the new names as examples; do not maintain a second catalogue of profile names in command text beyond those hints.
   - Alternative considered: enumerate every new profile in the onboard template. Rejected because discovery already returns the live set.

## Risks / Trade-offs

- [Apple guidance drifts from current SDK practice] → Keep documents to durable conventions (sandboxing, Swift concurrency, XCTest vs Swift Testing) rather than API lists that age quickly.
- [Users expect iPadOS as its own profile] → Document that iPadOS uses `ios`; add `ipados` later only if composition cannot express the difference.
- [Overlap between generic `testing` and Apple test-stack profiles] → `testing` stays language-neutral check guidance; Apple test profiles stay framework-specific.

## Migration Plan

- Ship the new YAML files and templates with the existing bundled resources. No project configuration migration is required.
- Existing projects gain the new profiles only when an agent applies them.
- Rollback is removal of the new profile files and templates; applied projects keep any patterns already merged into their categories.

## Open Questions

- Whether later language profiles (Ruby, Dart, and similar) should share this change's `language-profiles` capability or arrive as a follow-up change. Deferred; this wave stays at Swift and Objective-C.
