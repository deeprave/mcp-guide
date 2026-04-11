## 1. Add tracker feature flag
- [ ] 1.1 Define `tracker` flag schema: type string or dict with `type` and `project`/`repo` keys
- [ ] 1.2 Add flag validation: supported tracker types are `github`, `linear`, `jira`
- [ ] 1.3 Register flag in feature flag configuration and documentation

## 2. Implement tracker resolution module
- [ ] 2.1 Define async `TrackerClient` protocol with `resolve(ref)` and `list_open(filter)` methods
- [ ] 2.2 Implement `GitHubTrackerClient` using GitHub REST API (issues endpoint)
- [ ] 2.3 Implement `LinearTrackerClient` using Linear GraphQL API
- [ ] 2.4 Implement `JiraTrackerClient` using Jira REST API v3
- [ ] 2.5 Add authentication: env-var-based token lookup per tracker type
- [ ] 2.6 Wrap all network calls with timeout and graceful failure handling

## 3. Extend `:workflow/issue` command
- [ ] 3.1 Detect when argument is a tracker URL or bare issue ID
- [ ] 3.2 Call tracker resolution when `tracker` flag is configured
- [ ] 3.3 Map resolved fields to `issue`, `tracking`, `description` in workflow state
- [ ] 3.4 Fall back silently to manual entry if tracker resolution fails

## 4. Add tracker-aware queue population
- [ ] 4.1 On `:workflow/reset` or `:workflow/issue --next`, check for open tracker issues
- [ ] 4.2 Populate or suggest `queue` from tracker results when available
- [ ] 4.3 Make auto-population subject to `workflow-consent` rules

## 5. Add command and context templates
- [ ] 5.1 Update `:workflow/issue` command template to describe tracker resolution behaviour
- [ ] 5.2 Expose `workflow.tracker` context variable (type, configured status)

## 6. Tests and validation
- [ ] 6.1 Unit tests for each tracker client with mocked HTTP responses
- [ ] 6.2 Integration test for issue resolution flow in `:workflow/issue`
- [ ] 6.3 Validate change with `openspec validate add-tracker-integration --strict --no-interactive`
