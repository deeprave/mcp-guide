## 1. Onboarding State Flag

- [x] 1.1 Add `FLAG_ONBOARDED = "onboarded"` constant to `feature_flags/constants.py`
- [x] 1.2 Register validator: `validate_boolean_flag`, scope `PROJECT_ONLY` in `feature_flags/validators.py`

## 2. Startup Notification

- [x] 2.1 Extend `StartupInstructionListener._render_and_queue` to render `_onboard_prompt` after `_startup`
- [x] 2.2 Create `_system/_onboard_prompt.mustache` (`agent/instruction`, gated by `requires-onboarded: false`)
- [x] 2.3 Create `docs/onboard.mustache` (`user/information`) with user-facing notification content

## 3. Onboard Command

- [x] 3.1 Create `_commands/onboard.mustache` with full 12-dimension guided onboarding flow
- [x] 3.2 Include `--skip` / `?skip` path that sets `onboarded: true` and notifies user
- [x] 3.3 Step 4 sets `onboarded: true` as final step after user confirmation

## 4. Tests and Review

- [x] 4.1 Add unit tests for `StartupInstructionListener` covering all key paths
- [x] 4.2 Address all review findings
