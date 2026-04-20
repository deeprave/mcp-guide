## 1. Default Flag Normalization

- [x] 1.1 Add a shared default boolean-or-string validator for feature flags that do not register a more specific shape
- [x] 1.2 Add a shared default boolean-or-string normaliser that coerces canonical `"true"` and `"false"` string inputs to booleans while preserving other strings
- [x] 1.3 Update global and project feature flag mutation paths to apply the default normaliser unless a registered flag-specific normaliser overrides it

## 2. Registered Flag Compatibility

- [x] 2.1 Preserve existing custom validation and normalization behavior for structured built-in flags such as workflow lists, workflow consent mappings, and path flags
- [x] 2.2 Audit built-in feature flags and replace remaining hand-coded built-in flag names with `FLAG_` constants where appropriate
- [x] 2.3 Verify resolved feature flag reads continue to return canonical typed values after normalization, especially for boolean workflow-related flags

## 3. Verification

- [x] 3.1 Add or update unit tests covering default boolean-or-string validation and normalization for generic flags
- [x] 3.2 Add or update tests covering registered built-in flags to confirm the default scalar validator does not break supported structured values
- [x] 3.3 Add or update regression tests covering workflow requirement matching and related consumers when flags are set through string boolean inputs
