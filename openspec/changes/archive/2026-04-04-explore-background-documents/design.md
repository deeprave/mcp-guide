# Design notes: Research framework for efficient document ingestion

## Purpose

This document frames the exploration. It does not select an implementation architecture yet.

The exploration now treats ingestion as a combination of artifact preparation, execution staging, and the final ingestion step through `send_file_content`. The research should therefore compare candidate architectures against clear metrics rather than optimising prematurely around delegation alone.

## Import pipeline under study

The current high-level path is:

```
source -> agent acquires content -> agent prepares or relays content -> send_file_content -> MCP server -> DocumentTask -> store
```

Potential cost centres include:

- File read latency in the agent environment
- Time spent composing and transmitting large tool payloads
- Model/context overhead from relaying opaque content
- Queueing or processing latency after `send_file_content`
- User-facing wait time while the main conversation is blocked
- Artifact quality for later retrieval and use

These costs must be measured separately where possible.

## Shared and divergent parts of the pipeline

The exploration now treats the pipeline as:

```text
Shared:
  send_file_content -> DocumentTask -> add_document -> store

Client-side Track A:
  local-file acquisition and preparation

Client-side Track B:
  URL acquisition and preparation
```

The server-side path appears relatively lightweight and shared. The main divergence and likely bottleneck are client-side.

## Evaluation dimensions

Every candidate approach should be evaluated across the same dimensions:

- Foreground blocking time
- Total elapsed completion time
- Token/context overhead
- Artifact usefulness
- Context efficiency of the stored artifact
- Reliability and error visibility
- Portability across agent platforms
- Implementation and maintenance complexity

## Candidate architecture families

### Family A: Baseline workflow with better guidance

No new transport mechanism. Improve instructions, manifests, or operational guidance for the current import flow.

Questions:
- Is the main problem poor operator workflow rather than system design?
- Can batching or better conventions improve usability enough without new features?

### Family B: Agent-side delegated ingestion

The main agent identifies work, then hands the ingestion workflow to a separate worker that can still complete `send_file_content`.

Potential benefit:
- Improves foreground responsiveness if the main agent can continue working

Limitations:
- May not improve total throughput
- Depends heavily on platform-specific delegated-ingestion capabilities
- Needs robust status, retry, and completion reporting
- Only qualifies when the worker can complete ingestion end-to-end

### Family C: Helper abstractions over the current flow

Add templates, commands, or tools that validate inputs and prepare import tasks or manifests, while leaving the actual content relay to the agent.

Potential benefit:
- Better consistency
- Better validation before long-running work begins

Limitations:
- Does not by itself remove relay cost
- Risks packaging the current bottleneck rather than reducing it

### Family D: Alternative transport or batching strategies

Explore ways to reduce round trips or model involvement without assuming direct filesystem access by the server.

Examples to investigate:
- manifest-driven imports with chunked execution
- batched payload submission
- resumable import queues
- connector or handle-based imports where content identity can be passed without full inline payloads

This family may contain options that improve actual throughput rather than only foreground responsiveness.

### Family E: Platform-specific optimisations with fallback

Some agents may support richer background execution, blind relay patterns, or more direct file transfer mechanisms.

Questions:
- Which capabilities are genuinely available today?
- Can mcp-guide benefit from them without coupling its core design to one platform?
- What fallback exists for clients that lack those capabilities?

## Client and platform capability matrix

The exploration should record, at minimum:

- Whether the client supports background or delegated tasks
- Whether delegated workers retain the tool surface needed for `send_file_content`
- Whether task status and completion results can be queried reliably
- Whether large payload handling differs materially from the main agent path
- Whether the client exposes any non-standard mechanism that reduces relay cost
- Whether the client can access local files, connectors, or desktop-local resources in ways that materially change the import design
- Whether any optimisation is usable from both CLI and desktop variants, where relevant

Platforms of interest:

- Kiro
- Kiro CLI
- Codex
- Codex App on macOS
- Claude Code
- Claude Desktop
- Cursor
- cursor-agent
- GitHub Copilot
- Gemini CLI
- opencode-ai
- Windsurf
- Cascade
- Cline
- Generic MCP clients with no background support

The matrix should distinguish:

- product family,
- runtime form factor, such as CLI versus desktop,
- background capability,
- tool or connector capability,
- and whether the optimisation is portable or product-specific.

## Recommended matrix template

Each client entry should capture the following fields:

| Field | Description |
| --- | --- |
| Client | Product or runtime being evaluated |
| Form factor | CLI, desktop, editor-integrated agent, or hybrid |
| Local file access model | How the client reads local files, if at all |
| Background execution | None, limited, or full support |
| Delegation model | Natural language only, structured tasking, sub-agents, or equivalent |
| Tool reuse | Whether delegated work shares the MCP tools and permissions needed for ingestion |
| Status visibility | How progress and completion can be observed |
| Connector or remote file access | Whether the client can import from handles, connectors, or external sources |
| Relay-cost reduction potential | None, foreground-only, or possible throughput improvement |
| Portability notes | Whether the behaviour is broadly portable or product-specific |
| Risks | Known operational or UX limitations |

The matrix should be filled with observed behaviour where possible, and clearly marked hypotheses where behaviour has not yet been verified.

## Current client tiering

Based on the exploration so far:

- **Tier 1 strong delegated-ingestion candidates**
  - Kiro / Kiro CLI
  - Claude Code
  - Codex local / in-session
- **Currently not suitable for strict delegated ingestion**
  - Codex cloud
  - GitHub Copilot
  - Cursor / cursor-agent
  - Windsurf / Cascade
  - Claude Desktop
  - opencode-ai
  - Gemini CLI
  - Cline

Codex local / in-session was initially treated as conditional, but a direct background-worker test in Codex local behaved as desired: it created a separate worker, completed the requested work without blocking the main interaction, produced the requested output file, and later reported completion successfully. This is strong evidence that Codex local remains in scope for first-pass optimized support.

Cursor / cursor-agent was initially kept as a conditional candidate because its documented background-agent model looked promising. A stricter retry that explicitly required true background execution and actual file writing returned `BACKGROUND_UNAVAILABLE`, and no file was written. This is strong enough to treat Cursor as fallback-only for now unless a different Cursor-specific workflow is found and validated.

This tiering is specific to end-to-end delegated ingestion.

## Recommended candidate comparison template

Each candidate architecture family should be summarised in a comparison table such as:

| Candidate | Primary benefit | Likely downside | Helps foreground wait | Helps total throughput | Agent-agnostic | Operational complexity | Recommended next step |
| --- | --- | --- | --- | --- | --- | --- | --- |

Suggested candidate rows:

- Baseline workflow guidance
- Background delegation
- Helper abstraction or template
- Validation or manifest tool
- Alternative transport or batching
- Platform-specific optimisation with fallback

This table is intended to force a direct comparison between perceived user benefit and implementation cost.

## Artifact model

The exploration now leans toward:

```text
default
  prepared knowledge artifact

explicit alternate mode
  raw preservation
```

Additional conclusions:

- `agent/information` should be the default target type for both local-file and URL ingestion.
- Preparation should be driven by target type.
- Source format and noisiness should affect transformation intensity, not the intended artifact shape.
- Raw mode is primarily a local-file concern, with limited applicability to already-textual remote content.

## Recommended benchmark output

Benchmark notes should include:

- Document count
- Approximate payload size
- Client under test
- Import method under test
- Foreground wait time
- Total completion time
- Observable retries or failures
- Notes on operator effort

Where precise measurement is not possible, the notes should still record the method used and the level of confidence in the result.

## Failure model requirements

Any viable asynchronous or delegated approach must answer:

- How is file-not-found surfaced?
- How is invalid category or metadata surfaced?
- How is partial success reported?
- How are retries initiated and observed?
- How does the user know when a batch is complete?
- How can the main agent reconcile background results with later conversation state?
- Can the delegated worker actually complete `send_file_content` into the active MCP session?

If a candidate approach cannot answer these cleanly, it is probably not viable regardless of speed.

## Viability criteria for follow-up implementation

A follow-up implementation change should only be proposed if the exploration can show:

1. A measurable improvement in at least one primary metric that matters to users
2. No unacceptable regression in reliability or observability
3. A clear portability story:
   - agent-agnostic baseline, or
   - justified platform-specific optimisation with explicit fallback
4. A design that does not overcommit to a command or tool shape before the architecture is chosen
5. For any delegated path, proof that the worker can complete ingestion end-to-end rather than only offloading preparation

## Execution behavior contracts

### Optimized delegated branch

The optimized branch should:

1. Prefer separate execution only when the agent can still complete ingestion end-to-end
2. Preserve the same ingestion semantics:
   - acquire
   - apply raw/prepared rules
   - prepare toward target type
   - call `send_file_content`
3. Keep the main interaction available
4. Acknowledge the separate execution briefly
5. Return a final completion or failure summary
6. Fall back inline, with a brief explanation, if separate execution cannot actually be used

### Universal fallback branch

The fallback branch should:

1. Perform the same ingestion workflow inline
2. Preserve the same artifact semantics and `send_file_content` step
3. Optionally warn briefly if the work may take noticeable time
4. Return a direct completion or failure result
5. Use standardized fallback explanation wording whenever optimized separate execution is unavailable or cannot actually be used

## Template design direction

Current template-design bias:

- execution-first top-level branching
- source-specific semantic partials beneath it
- capability-oriented membership flags for branching
- readability over maximum DRYness

The shared optimized branch should describe the required behavior rather than overcommitting to product-specific mechanism names.

## Expected research outputs

- Benchmark notes for current import behaviour
- A capability matrix across the target client matrix
- A comparison table of candidate families
- A recommendation memo naming the preferred next step, if any
- Clear separation between verified findings and unverified assumptions
