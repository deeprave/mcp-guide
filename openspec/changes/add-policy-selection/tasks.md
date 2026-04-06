# Tasks: add-policy-selection

- [x] 1. Add the default `policies` category to the default profile and ensure it is discoverable through the existing profile/category system
- [x] 2. Define the first-pass policy topic structure for high-value areas such as git ops, commit/pr behavior, testing, methodology, quality, style, toolchain, tooling prohibitions, and review
- [x] 3. Audit existing user-facing templates and markdown documents to identify embedded optional preferences that should move into policy documents
- [x] 4. Create the first-pass policy corpus as standalone policy documents under the `policies` category, organized by topic (71 documents across git, testing, methodology, quality, style, toolchain, tooling, pr, review)
- [ ] 5. Update core guidance documents and templates to remove extracted opinionated choices or replace them with neutral guidance and policy-topic references
      > **Deferred** — depends on `add-category-topics` (policy pre-rendering and sub-path filtering must be implemented before templates can reference `{{> policy/topic}}`)
- [ ] 6. Implement project-level composition/selection support for policy documents using existing categories, collections, profiles, or related project configuration
      > **Partially available** — users can set patterns on the `policies` category now; full `{{> topic}}` resolution depends on `add-category-topics`
- [ ] 7. Implement guide resource resolution for selected policy topics such as `guide://policies/<topic>`
      > **Deferred** — moved to `add-category-topics` (requires sub-path filtering and discover_category_documents)
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
