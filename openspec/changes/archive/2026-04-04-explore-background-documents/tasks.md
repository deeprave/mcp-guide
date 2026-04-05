## 1. Benchmark the current import path
- [x] 1.1 Measure single-document import timing end to end
- [x] 1.2 Measure batch import timing for 3 to 5 documents
- [x] 1.3 Break timings down where possible into file read, tool relay, and server-side processing
- [x] 1.4 Record which metric matters most: artifact usefulness, context efficiency, UX responsiveness, or total completion time
- [x] 1.5 Capture results in a consistent benchmark note format

## 2. Map the solution space
- [x] 2.1 Document candidate architecture families, not just delegation-based ones
- [x] 2.2 Identify which options improve responsiveness only, which improve artifact quality, and which may improve true throughput
- [x] 2.3 Record constraints that apply across all MCP clients
- [x] 2.4 Summarise candidate families in a comparison table with benefits, limitations, and portability notes
- [x] 2.5 Separate local-file acquisition/preparation from URL acquisition/preparation explicitly

## 3. Assess the target client matrix
- [x] 3.1 Validate Kiro and Kiro CLI as Tier 1 delegated-ingestion candidates
- [x] 3.2 Validate Claude Code as a Tier 1 delegated-ingestion candidate
- [x] 3.3 Determine whether Codex local / in-session should remain a Tier 2 candidate or be deferred
- [x] 3.4 Determine whether Cursor / cursor-agent should remain a Tier 2 candidate or be deferred
- [x] 3.5 Record why Codex cloud, GitHub Copilot, Gemini CLI, Cline, Claude Desktop, Windsurf / Cascade, and opencode-ai do not currently qualify for strict delegated ingestion
- [x] 3.6 Identify the minimum agent-agnostic fallback that works across the full target matrix
- [x] 3.11 Record findings in a consistent client capability matrix
- [x] 3.12 Mark each matrix row as verified, partially verified, or hypothetical

Notes:

- 3.3 resolved: direct Codex local background-worker testing indicates Codex local / in-session should remain in scope for first-pass optimized support rather than being deferred.
- 3.4 resolved: a stricter Cursor retry that explicitly required true background execution and actual file writing returned `BACKGROUND_UNAVAILABLE`, so Cursor / cursor-agent should be treated as fallback-only for now unless a different product-specific workflow is validated.

## 4. Define operational requirements
- [x] 4.1 Determine how progress, completion, and partial failure should surface to the user
- [x] 4.2 Determine retry and reconciliation requirements for asynchronous imports
- [x] 4.3 Define what makes an approach operationally acceptable beyond raw speed, including artifact usefulness and context efficiency
- [x] 4.4 Separate operational requirements that are mandatory from those that are merely desirable
- [x] 4.5 Define the behavior contract for the optimized delegated branch
- [x] 4.6 Define the behavior contract for the universal fallback branch

## 5. Make a recommendation
- [x] 5.1 Compare candidate approaches against the agreed evaluation dimensions
- [x] 5.2 Recommend one of the following outcomes
- [x] 5.3 No product change, documented workflow guidance only
- [x] 5.4 Agent-agnostic helper abstraction
- [x] 5.5 Narrow Tier 1 platform-specific optimisation with explicit fallback
- [x] 5.6 Follow-up implementation change with explicit viability criteria
- [x] 5.7 Publish a recommendation memo that separates verified findings from open assumptions

Notes:

- This exploration is complete.
- The findings were captured in `.todo/explore-background-documents-exploration.md` and `.todo/explore-document-ingestion-summary.md`.
- The practical implementation outcome was carried forward into the follow-on change `improve-ux-documents`.
