## 1. Command rendering and selection context

- [x] 1.1 Add the packaged `skills/export` command template with one positional skill name and a `force` keyword, and verify it is discoverable through prompt and `guide://_skills/export/<skill-name>` command surfaces
- [x] 1.2 Provide project-aware available-skill and canonical `.agents/skills` context to the command template, and verify no alternate destination or multi-skill input is rendered
- [x] 1.3 Validate the named public skill against the current skill catalogue, and verify empty and unavailable names cannot produce an export instruction

## 2. Export interaction contract

- [x] 2.1 Render native-picker guidance for an omitted skill name, and verify the command presents the complete single-select skill set
- [x] 2.2 Render a non-interactive textual fallback that waits for one selected name, and verify it does not direct an export before that answer is supplied
- [x] 2.3 Render existing-target inspection and `force=true` guidance, including temporary backup, removal, and restoration behaviour

## 3. Package export guidance

- [x] 3.1 Instruct the agent to retrieve the named rendered `SKILL.md` resource for the current session and write it below `.agents/skills`, treating it as a user-owned one-way snapshot, and verify completion guidance reports the created path
- [x] 3.2 Document optional package-member retrieval and script safety in the command help, and verify the instructions never direct server-side script execution or global-project writes
- [x] 3.3 When `.claude` exists, create `.claude/skills` as necessary and link absent Claude skill entries to their canonical export; preserve and warn about non-matching existing entries

## 4. Validation and documentation

- [x] 4.1 Add focused command-selection and catalogue-validation tests without asserting production instruction text
- [x] 4.2 Update user and developer documentation for current-project skill export, supported URI arguments, interactive selection, forced replacement, Claude compatibility, and package output structure

## 5. Review follow-up

- [x] 5.1 Return a complete rendered package from a bound `export_skill` tool through MIME, including portable entrypoint frontmatter and member permissions.
- [x] 5.2 Update export command and dynamic help to use the tool and accurately describe confirmation, replacement, package output, and Claude-link behaviour.
- [x] 5.3 Add behavioural coverage for the package export result and help output without asserting production-document text.
