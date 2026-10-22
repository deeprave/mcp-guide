# Tasks

## 1. Template-language profile content

- [ ] 1.1 Add bundled `jinja2` and `chevron` profile definitions that select only their matching `lang/` guidance; verify `list_profiles` discovers both names and each profile applies idempotently to a project.
- [ ] 1.2 Add concise Jinja2 guidance covering syntax, inheritance/includes, auto-escaping, safe data handling, whitespace control, and behaviour-focused validation; verify it is rendered through the `lang/jinja2` expression after applying the profile.
- [ ] 1.3 Add concise Chevron/Mustache guidance covering variables, sections, inverted sections, partials, escaping, expression limits, and behaviour-focused validation; verify it is rendered through the `lang/chevron` expression after applying the profile.

## 2. User guidance and verification

- [ ] 2.1 Update the profile catalogue documentation to list Jinja2 and Chevron as additive template-language profiles and show their composition with other profiles; verify every named profile exists.
- [ ] 2.2 Add behavioural tests for discovery, application, idempotency, and rendered language guidance without asserting repository-owned template prose; run the focused profile and content-rendering pytest tests.
- [ ] 2.3 Run the relevant full test suite and `openspec validate add-template-languages --strict`; verify the change satisfies its profile and documentation scenarios.
