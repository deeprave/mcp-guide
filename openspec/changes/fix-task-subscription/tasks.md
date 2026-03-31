## 1. Fix dispatch_event subscription iteration
- [x] 1.1 Iterate a copy of `self._subscriptions` instead of the live list
- [x] 1.2 Remove the `active_subscriptions` accumulator and the final `self._subscriptions = active_subscriptions` overwrite
- [x] 1.3 Handle dead weak reference cleanup separately (filter in-place before iteration)

## 2. Validation
- [x] 2.1 Run full test suite — 1738 passed
- [ ] 2.2 Manual verification: status should show reduced active task count in steady state after flags resolve
