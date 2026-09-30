# Tasks

## 1. Retire the handoff command

- [x] 1.1 Remove the `:handoff` command template and confirm `guide://_handoff` is no longer a discovered command
- [x] 1.2 Drop the handoff command requirement and the `save-context` / `restore-context` scenarios from the living specs, and confirm generic alias behaviour still resolves a query-bearing alias

## 2. Workflow command input

- [x] 2.1 Request the four current-repository review choices, with branch-name and pull-request-number follow-ups, and verify a supplied target renders its comparison without asking again
- [x] 2.2 Fill the phase choice from the enabled workflow phases excluding the active phase, skip it when a phase is already supplied, provide a render fallback, and verify an unknown phase is rejected without a workflow-file update
- [x] 2.3 Remove all server-side Git inspection and require the calling agent to apply reset branch, completion, and stash guards in its own checkout, including reset with an explicit issue identifier
- [x] 2.4 Render no-target review guidance when its elicitation supplier is unavailable or cancelled, and retain a defensive unsupported-mode fallback
- [x] 2.5 Update workflow and elicitation authoring documentation, remove retired handoff fixture references, and share workflow phase normalisation

## 3. Tests

- [x] 3.1 Run focused behavioural and command-input tests without asserting production template content, then run `openspec validate update-elicitation-commands --strict`

## 4. OpenSpec synchronisation

- [x] 4.1 Synchronise all delta specifications consistently before archiving the change
