## 1. Apple platform profiles

- [ ] 1.1 Add bundled `ios`, `macos`, `watchos`, `tvos`, and `visionos` profiles that each add the matching `lang` pattern, and verify `list_profiles` returns those names.
- [ ] 1.2 Add `lang/` guidance documents for each Apple platform, and verify applying each profile renders non-empty language content for that platform.

## 2. Language profiles

- [ ] 2.1 Add bundled `swift` and `objective-c` profiles with matching `lang/` guidance, and verify applying each profile renders the corresponding language heading.
- [ ] 2.2 Apply `swift` then `ios` on one project and verify both selections persist and a second apply of either profile does not duplicate patterns.

## 3. Test profiles

- [ ] 3.1 Add a bundled `testing` profile that selects the existing `checks` `testing` pattern, and verify applying it includes the existing testing check guidance without changing testing-policy patterns.
- [ ] 3.2 Add bundled `xctest` and `swift-testing` profiles with matching guidance, and verify they compose so both test-stack selections remain when applied together.

## 4. Onboarding and documentation

- [ ] 4.1 Update onboarding inspection hints for Xcode, Swift package, and Apple test-stack markers, and verify the onboard command still stages profiles through `list_profiles` rather than a hard-coded catalogue.
- [ ] 4.2 Update user profile documentation to mention the new Apple, language, and test-stack profiles, and verify every named example refers to a profile that exists.

## 5. Verification

- [ ] 5.1 Add focused profile application tests for the new profiles and composition cases, then run `uv run pytest tests/integration/test_profile_application.py tests/unit/test_profile.py` in the foreground and verify they pass.
- [ ] 5.2 Run `openspec validate add-language-profiles --type change --strict` and verify no validation errors remain.
