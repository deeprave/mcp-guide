## 1. Command rendering and selection context

- [ ] 1.1 Add the packaged `skills/export` command template with parsed positional destination and `skills` keyword handling, and verify it is discoverable through prompt and `guide://_skills/export` command surfaces
- [ ] 1.2 Provide project-aware available-skill and current-agent destination context to the command template, and verify the default `.agents`, recognised agent-specific alternatives, and explicit relative destination render correctly
- [ ] 1.3 Validate selected comma-separated public skill names against the current skill catalogue, and verify empty, duplicate, and unavailable selections cannot produce a partial export instruction

## 2. Export interaction contract

- [ ] 2.1 Render native-picker guidance for omitted destinations and omitted skill selections, and verify the command presents the default/current-agent alternatives and the complete multi-select skill set
- [ ] 2.2 Render a non-interactive textual fallback that waits for destination and selection answers, and verify it does not direct an export before those answers are supplied
- [ ] 2.3 Render a final user-confirmation step with resolved package output paths and overwrite inspection, and verify rejected or absent confirmation prevents write instructions

## 3. Package export guidance

- [ ] 3.1 Instruct the agent to retrieve each selected rendered `SKILL.md` resource and write it into a package rooted below the current project destination, and verify completion guidance reports the destination and created paths
- [ ] 3.2 Document optional package-member retrieval and script safety in the command help, and verify the instructions never direct server-side script execution or global-project writes

## 4. Validation and documentation

- [ ] 4.1 Add focused command-rendering and URI integration tests covering explicit/default destinations, selection, confirmation, unavailable names, and project containment
- [ ] 4.2 Update user and developer documentation for current-project skill export, supported URI arguments, destination selection, interactive fallbacks, and package output structure
- [ ] 4.3 Run the focused tests, formatting, type checks, strict OpenSpec validation, and the required full test suite, recording any failures before preparing a pull request
