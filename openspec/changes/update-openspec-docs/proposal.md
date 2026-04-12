# Change: Update OpenSpec Documentation

## Why

The OpenSpec documentation has drifted from the implemented behavior in a few
important places. In particular, the docs currently imply that OpenSpec change
data is refreshed proactively on an hourly basis, but the implementation no
longer does that. The running `OpenSpecTask` timer exists to invalidate cached
change data once it becomes stale; fresh data is then fetched on demand when an
OpenSpec command needs it.

Because documentation issues like this are likely to arise over time, it is
useful to keep a standing documentation-focused OpenSpec change that can absorb
further doc corrections and clarifications as they are identified.

## What Changes

- Update OpenSpec-related user and developer documentation so it matches the
  current implementation
- Clarify that OpenSpec change/status/show data may be cached, but is not
  refreshed proactively on an hourly timer
- Clarify that the `OpenSpecTask` hourly timer exists to invalidate cached
  change data after the cache ages out, not to fetch fresh OpenSpec data
- Use this change as a standing documentation proposal for future OpenSpec doc
  corrections and clarifications

## Impact

- Affected specs: documentation-related capability specs as needed
- Likely affected code/docs:
  - `docs/user/openspec.md`
  - any guide or help templates that describe OpenSpec cache/timer behavior
  - related OpenSpec-facing spec text if current wording is misleading
- No runtime behavior changes intended
