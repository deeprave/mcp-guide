# Fix Task Subscription Lifecycle

**Status**: Proposed
**Priority**: High
**Complexity**: Low

## Why

Tasks that call `unsubscribe(self)` during event handling are silently re-subscribed. The status display shows 6 active tasks when only 2–3 should be running in steady state.

The root cause is in `TaskManager.dispatch_event`:

1. It iterates `self._subscriptions` directly, building a local `active_subscriptions` list
2. Each subscription is appended to `active_subscriptions` before `handle_event` is called
3. If `handle_event` calls `unsubscribe(self)`, that correctly removes the subscriber from `self._subscriptions`
4. But at the end of the loop, `self._subscriptions = active_subscriptions` overwrites the mutation — the unsubscribed task is still in `active_subscriptions` and gets restored

This affects every task that unsubscribes during event dispatch:
- **ClientContextTask**: `_initialise` → `unsubscribe` when `allow-client-info` flag disabled — overwritten
- **McpUpdateTask**: `handle_event` → `finally: unsubscribe` after one-shot — overwritten
- **WorkflowMonitorTask**: `_initialise` → `unsubscribe` when `workflow` flag disabled — overwritten

**RetryTask** is not directly affected (unsubscribes from timer, not during dispatch), but its `get_subscription_count() == 1` self-check never triggers because the other tasks linger due to this bug.

## What Changes

- `dispatch_event` should iterate a **copy** of `self._subscriptions`, allowing mutations on the original collection during dispatch to take effect
- Remove the `active_subscriptions` list and the final `self._subscriptions = active_subscriptions` assignment — dead subscriber cleanup (weak ref check) can filter in-place or use a different mechanism
