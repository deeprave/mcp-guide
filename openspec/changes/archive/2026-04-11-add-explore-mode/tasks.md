## 1. Add workflow phase support
- [x] 1.1 Add `exploration` as a valid workflow phase
- [x] 1.2 Ensure workflow phase configuration distinguishes ordered phases from non-ordered available phases
- [x] 1.3 Add `exploration` to the default available phase set

## 2. Add command and phase templates
- [x] 2.1 Create `_commands/workflow/explore.mustache`
- [x] 2.2 Add alias `explore` for the new command
- [x] 2.3 Create `_workflow/06-exploration.mustache`
- [x] 2.4 Keep the phase guidance concise, research-oriented, and explicitly non-implementing

## 3. Implement issue-handling behavior
- [x] 3.1 Mirror `:workflow/discuss` behavior for issue retention when no argument is supplied
- [x] 3.2 Support optional explicit issue switching in `:workflow/explore <issue>`
- [x] 3.3 Ensure explicit entry into exploration preserves the current issue unless the user changes it

## 4. Implement exploration trigger behavior
- [x] 4.1 Detect when the current issue starts with `explor`
- [x] 4.2 Treat that as a suggestion trigger for exploration mode
- [x] 4.3 Ask the user before entering exploration mode
- [x] 4.4 Do not switch to exploration automatically

## 5. Implement transition rules
- [x] 5.1 Require explicit consent to leave exploration
- [x] 5.2 Ensure exploration can be entered without forcing the normal ordered workflow sequence
- [x] 5.3 Ensure existing ordered transitions remain intact

## 6. Update specs and validation
- [x] 6.1 Add spec deltas for workflow flags/configuration
- [x] 6.2 Add spec deltas for workflow commands/context
- [x] 6.3 Add spec deltas for help/template exposure if needed
- [x] 6.4 Validate the change with strict OpenSpec validation
