## 1. Package identity and discovery

- [ ] 1.1 Define and validate the required unique public `name` in skill entrypoint frontmatter, and verify missing, blank, invalid, and duplicate names leave packages unavailable with diagnostics
- [ ] 1.2 Extend the cached skill discovery path to find nested `SKILL.md` package roots and map each declared name to its package root, and verify flat and nested package discovery together
- [ ] 1.3 Add declared names to bundled skill entrypoints and verify the existing catalogue retains their current public names

## 2. Resolution and catalogue

- [ ] 2.1 Resolve entrypoints and members from the public name-to-package mapping while retaining literal-member containment checks, and verify a nested package responds to its flat `guide://$<name>` URI
- [ ] 2.2 Keep catalogue, list_skills, prompt, and native resource results keyed by the declared public name, and verify no server-side directory path is exposed
- [ ] 2.3 Preserve flat-package compatibility and verify existing skill resource and prompt calls retain their public URIs

## 3. Verification and documentation

- [ ] 3.1 Add focused tests for nested discovery, duplicate-name rejection, nested member retrieval, and unchanged flat-package retrieval, and verify the targeted pytest suite passes
- [ ] 3.2 Update skill authoring documentation with public-name and hierarchy rules, and verify documented examples match the resource contract
- [ ] 3.3 Run strict OpenSpec validation and relevant foreground pytest and static checks, and record results in the workflow handover context
