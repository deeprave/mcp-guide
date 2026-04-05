# Tasks: add-policy-selection

- [ ] 1. Add the default `policy` category to the default profile and ensure it is discoverable through the existing profile/category system
- [ ] 2. Define the first-pass policy topic structure for high-value areas such as scm, commit/pr behavior, workflow mode, testing, type checking, and toolchain preferences
- [ ] 3. Audit existing user-facing templates and markdown documents to identify embedded optional preferences that should move into policy documents
- [ ] 4. Extract the first-pass embedded preferences into standalone policy documents or templates under the `policy` category
- [ ] 5. Update core guidance documents and templates to remove extracted opinionated choices or replace them with neutral guidance and policy-topic references
- [ ] 6. Implement project-level composition/selection support for policy documents using existing categories, collections, profiles, or related project configuration
- [ ] 7. Implement guide resource resolution for selected policy topics such as `guide://policy/<topic>`
- [ ] 8. Add or update tests covering:
- [ ] 8.1 default policy category availability
- [ ] 8.2 policy selection/composition behavior
- [ ] 8.3 selected policy guide-resource resolution
- [ ] 8.4 neutralized core guidance where policy extraction occurred
- [ ] 9. Validate the change end-to-end with:
- [ ] 9.1 `openspec validate add-policy-selection --strict`
- [ ] 9.2 `uv run ty check src/`
- [ ] 9.3 `uv run pytest -q`
- [ ] 10. Record follow-on gaps or onboarding dependencies that should be handled in `add-guided-onboarding`
